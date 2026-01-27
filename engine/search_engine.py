class DatabaseSearchEngine:
    def __init__(self, database_manager):
        self.db_manager = database_manager
    
    def search_all_tables(self, search_term, max_results_per_table=50):
        """Search across all tables in the database for the given term"""
        if not search_term or not search_term.strip():
            return []
        
        search_term = search_term.strip()
        tables = self.db_manager.get_tables()
        results = []
        
        for table_name in tables:
            if table_name.endswith('_filtered'):
                continue
            
            try:
                # Get table columns
                columns_query = f"PRAGMA table_info('{table_name}')"
                columns_result = self.db_manager.execute_query(columns_query)
                columns = [col[1] for col in columns_result]
                
                # Build search query for all text/varchar columns
                where_conditions = []
                for col in columns:
                    where_conditions.append(f"CAST({col} AS VARCHAR) LIKE '%{search_term}%'")
                
                if where_conditions:
                    where_clause = ' OR '.join(where_conditions)
                    query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT {max_results_per_table}"
                    
                    rows = self.db_manager.execute_query(query)
                    
                    if rows:
                        results.append({
                            'table': table_name,
                            'columns': columns,
                            'rows': rows,
                            'count': len(rows)
                        })
            except Exception as e:
                print(f"Error searching table {table_name}: {str(e)}")
                continue
        
        return results
