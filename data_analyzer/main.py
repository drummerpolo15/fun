#!/usr/bin/env python3
"""
Data Analysis and Visualization Tool
Main entry point for interactive data analysis with natural language queries.
Supports both file-based datasets and MySQL database connections.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from data_loader import DataLoader
from query_analyzer import QueryAnalyzer
from data_analyzer import DataAnalyzer
from visualizer import Visualizer
from db_connection import DatabaseConnection
from question_suggester import QuestionSuggester
from sql_query_generator import SQLQueryGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataAnalysisTool:
    """Main class for data analysis and visualization."""
    
    def __init__(self, data_file: Optional[str] = None, output_dir: str = "visualizations",
                 db_connection: Optional[DatabaseConnection] = None):
        """
        Initialize the data analysis tool.
        
        Args:
            data_file: Path to the dataset file (if using file mode)
            output_dir: Directory to save visualizations
            db_connection: Database connection object (if using database mode)
        """
        self.db_connection = db_connection
        self.is_database_mode = db_connection is not None
        
        if self.is_database_mode:
            # Database mode
            self.data_loader = DataLoader(db_connection=db_connection)
            self.question_suggester = QuestionSuggester(db_connection)
            self.schema = None
            self.sql_generator = None
            
            # Analyze database schema
            logger.info("Analyzing database schema...")
            self.schema = self.question_suggester.analyze_database()
            self.sql_generator = SQLQueryGenerator(self.schema)
            
            # Print database summary
            self._print_database_summary()
        else:
            # File mode
            if data_file is None:
                raise ValueError("Either data_file or db_connection must be provided")
            
            self.data_loader = DataLoader()
            self.query_analyzer = QueryAnalyzer()
            self.visualizer = Visualizer(output_dir)
            self.data_analyzer = None
            
            # Load the dataset
            logger.info(f"Loading dataset from: {data_file}")
            self.data = self.data_loader.load_file(data_file)
            self.data_analyzer = DataAnalyzer(self.data)
            
            # Print dataset summary
            summary = self.data_loader.get_summary()
            self._print_summary(summary)
        
        # Initialize visualizer for both modes
        self.visualizer = Visualizer(output_dir)
    
    def _print_summary(self, summary: dict):
        """Print a summary of the loaded dataset."""
        print("\n" + "="*60)
        print("DATASET SUMMARY")
        print("="*60)
        print(f"File: {summary['metadata']['file_name']}")
        print(f"Shape: {summary['shape'][0]} rows × {summary['shape'][1]} columns")
        print(f"\nColumns: {', '.join(summary['columns'])}")
        
        if summary.get('numeric_summary'):
            print(f"\nNumeric columns: {len(summary['numeric_summary'])}")
        if summary.get('categorical_summary'):
            print(f"Categorical columns: {len(summary['categorical_summary'])}")
        
        print("="*60 + "\n")
    
    def _print_database_summary(self):
        """Print a summary of the database."""
        print("\n" + "="*60)
        print("DATABASE SUMMARY")
        print("="*60)
        print(f"Database: {self.schema.get('database', 'N/A')}")
        print(f"Host: {self.db_connection.host}")
        
        tables = self.schema.get('tables', {})
        print(f"\nTables: {len(tables)}")
        
        for table_name, table_info in tables.items():
            row_count = table_info.get('row_count', 0)
            columns = table_info.get('columns', [])
            print(f"\n  {table_name}:")
            print(f"    Rows: {row_count:,}")
            print(f"    Columns ({len(columns)}): {', '.join(columns[:10])}")
            if len(columns) > 10:
                print(f"    ... and {len(columns) - 10} more")
        
        print("="*60 + "\n")
    
    def process_query(self, query: str, show_suggestions: bool = True) -> dict:
        """
        Process a natural language query and generate visualization.
        
        Args:
            query: Natural language query string
            show_suggestions: Whether to show question suggestions after processing (database mode only)
            
        Returns:
            Dictionary containing analysis results and visualization path
        """
        logger.info(f"Processing query: {query}")
        
        if self.is_database_mode:
            return self._process_database_query(query, show_suggestions)
        else:
            return self._process_file_query(query)
    
    def _process_file_query(self, query: str) -> dict:
        """Process a query in file mode."""
        # Analyze the query
        available_columns = list(self.data.columns)
        query_params = self.query_analyzer.analyze(query, available_columns)
        
        # Perform analysis
        analysis_result = self.data_analyzer.analyze(query_params)
        
        # Generate visualization
        visualization_path = self.visualizer.create_visualization(analysis_result, query_params)
        
        # Print results
        self._print_results(analysis_result, query_params)
        print(f"\nVisualization saved to: {visualization_path}\n")
        
        return {
            'query_params': query_params,
            'analysis_result': analysis_result,
            'visualization_path': visualization_path
        }
    
    def _process_database_query(self, query: str, show_suggestions: bool = True) -> dict:
        """Process a query in database mode."""
        # Generate SQL query
        query_info = self.sql_generator.generate_query(query)
        sql_query = query_info['sql']
        table_name = query_info['table_name']
        query_params = query_info['query_params']
        
        # Display the SQL query
        print("\n" + "="*60)
        print("SQL QUERY")
        print("="*60)
        print(sql_query)
        print("="*60)
        
        # Execute SQL query
        try:
            data = self.db_connection.execute_query(sql_query)
            
            if data.empty:
                print("\nQuery returned no results.")
                return {
                    'sql_query': sql_query,
                    'query_params': query_params,
                    'data': None
                }
            
            # Create data analyzer for the results
            data_analyzer = DataAnalyzer(data)
            
            # Perform analysis on the results
            analysis_result = data_analyzer.analyze(query_params)
            
            # Generate visualization
            visualization_path = self.visualizer.create_visualization(analysis_result, query_params)
            
            # Print results
            self._print_results(analysis_result, query_params)
            print(f"\nVisualization saved to: {visualization_path}\n")
            
            # Show suggested questions
            if show_suggestions:
                self._show_suggested_questions()
            
            return {
                'sql_query': sql_query,
                'query_params': query_params,
                'analysis_result': analysis_result,
                'visualization_path': visualization_path
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}", exc_info=True)
            print(f"\nError executing query: {str(e)}\n")
            raise
    
    def _show_suggested_questions(self):
        """Display suggested questions based on database analysis."""
        try:
            suggestions = self.question_suggester.get_question_suggestions()
            
            if suggestions:
                print("\n" + "="*60)
                print("SUGGESTED QUESTIONS")
                print("="*60)
                print("Based on the database structure, here are some interesting questions you might want to ask:\n")
                
                for i, suggestion in enumerate(suggestions[:10], 1):
                    question = suggestion.get('question', 'N/A')
                    sql = suggestion.get('query', 'N/A')
                    category = suggestion.get('category', 'general')
                    
                    print(f"{i}. {question}")
                    print(f"   Category: {category}")
                    print(f"   SQL: {sql}")
                    print()
                
                print("="*60 + "\n")
        except Exception as e:
            logger.warning(f"Error generating suggestions: {e}")
    
    def _print_results(self, analysis_result: dict, query_params: dict):
        """Print analysis results in a readable format."""
        print("\n" + "-"*60)
        print("ANALYSIS RESULTS")
        print("-"*60)
        print(f"Intent: {query_params.get('intent', 'unknown')}")
        print(f"Chart type: {query_params.get('chart_type', 'N/A')}")
        
        if 'error' in analysis_result:
            print(f"\nError: {analysis_result['error']}")
            return
        
        analysis_type = analysis_result.get('analysis_type', 'unknown')
        print(f"Analysis type: {analysis_type}")
        
        # Print specific results based on analysis type
        if analysis_type == 'statistics':
            results = analysis_result.get('results', {})
            if 'mean' in results:
                print("\nMeans:")
                for col, val in results['mean'].items():
                    print(f"  {col}: {val:.2f}")
        
        elif analysis_type == 'aggregation':
            data = analysis_result.get('data')
            if data is not None and not data.empty:
                print(f"\nAggregated data (first 10 rows):")
                print(data.head(10).to_string())
        
        elif analysis_type == 'distribution':
            stats = analysis_result.get('statistics', {})
            if stats:
                print(f"\nDistribution statistics for {analysis_result.get('column')}:")
                print(f"  Mean: {stats.get('mean', 'N/A'):.2f}")
                print(f"  Median: {stats.get('median', 'N/A'):.2f}")
                print(f"  Std Dev: {stats.get('std', 'N/A'):.2f}")
        
        elif analysis_type == 'correlation':
            print("\nCorrelation analysis completed. See heatmap visualization.")
        
        elif analysis_type == 'trend':
            print("\nTrend analysis completed. See line chart visualization.")
        
        print("-"*60)
    
    def interactive_mode(self):
        """Run in interactive mode, accepting queries from user input."""
        print("\n" + "="*60)
        print("INTERACTIVE DATA ANALYSIS MODE")
        print("="*60)
        print("Enter your questions about the dataset.")
        print("Type 'exit', 'quit', or 'q' to exit.")
        print("Type 'summary' to see dataset summary again.")
        print("="*60 + "\n")
        
        while True:
            try:
                query = input("Query: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\nExiting...")
                    break
                
                if query.lower() == 'summary':
                    if self.is_database_mode:
                        self._print_database_summary()
                    else:
                        summary = self.data_loader.get_summary()
                        self._print_summary(summary)
                    continue
                
                if query.lower() == 'suggestions':
                    if self.is_database_mode:
                        self._show_suggested_questions()
                    else:
                        print("\nSuggestions are only available in database mode.\n")
                    continue
                
                # Process the query
                self.process_query(query)
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                print(f"\nError: {str(e)}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive data analysis and visualization tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # File mode - Interactive
  python main.py data.csv
  
  # File mode - Single query
  python main.py data.csv --query "What is the average age?"
  
  # Database mode - Interactive
  python main.py --db-host localhost --db-user root --db-password pass --db-name mydb
  
  # Database mode - Single query
  python main.py --db-host localhost --db-user root --db-password pass --db-name mydb --query "What is the average salary?"
  
  # Custom output directory
  python main.py data.csv --output my_charts/
        """
    )
    
    # Data source arguments (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        'data_file',
        nargs='?',
        help='Path to the dataset file (CSV, JSON, Excel, etc.)'
    )
    
    # Database connection arguments
    parser.add_argument(
        '--db-host',
        help='MySQL database host'
    )
    parser.add_argument(
        '--db-user',
        help='MySQL database username'
    )
    parser.add_argument(
        '--db-password',
        help='MySQL database password'
    )
    parser.add_argument(
        '--db-name',
        help='MySQL database name'
    )
    parser.add_argument(
        '--db-port',
        type=int,
        default=3306,
        help='MySQL database port (default: 3306)'
    )
    
    parser.add_argument(
        '--query', '-q',
        help='Single query to process (if not provided, runs in interactive mode)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='visualizations',
        help='Output directory for visualizations (default: visualizations)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Determine mode (database or file)
        if args.db_host and args.db_user and args.db_name:
            # Database mode
            if not args.db_password:
                # Try to get password from environment or prompt
                import getpass
                args.db_password = getpass.getpass("Enter database password: ")
            
            db_connection = DatabaseConnection(
                host=args.db_host,
                user=args.db_user,
                password=args.db_password,
                database=args.db_name,
                port=args.db_port
            )
            
            tool = DataAnalysisTool(output_dir=args.output, db_connection=db_connection)
            
            if args.query:
                tool.process_query(args.query)
            else:
                tool.interactive_mode()
            
            # Close database connection
            db_connection.close()
            
        elif args.data_file:
            # File mode
            tool = DataAnalysisTool(args.data_file, args.output)
            
            if args.query:
                tool.process_query(args.query)
            else:
                tool.interactive_mode()
        else:
            parser.error("Either data_file or database connection arguments (--db-host, --db-user, --db-name) are required")
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

