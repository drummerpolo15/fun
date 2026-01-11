# Data Analyzer and Visualization Tool

An interactive Python tool that allows you to ask natural language questions about your datasets and automatically generates visualizations based on the analysis. Supports both file-based datasets and MySQL database connections.

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Automatic Analysis**: The tool analyzes your query and performs appropriate statistical analysis
- **Smart Visualizations**: Automatically generates appropriate charts and graphs
- **Multiple Data Formats**: Supports CSV, JSON, Excel, Parquet, and Feather files
- **MySQL Database Support**: Connect to MySQL databases and query them using natural language
- **SQL Query Display**: See the SQL queries generated from your natural language queries
- **Question Suggestions**: Get intelligent suggestions for interesting questions based on database structure
- **Interactive Mode**: Run queries interactively or pass a single query via command line

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### File Mode

#### Interactive Mode

Run the tool with a dataset file to enter interactive mode:

```bash
python main.py your_data.csv
```

Then ask questions about your data:

```
Query: What is the average age?
Query: Show me the distribution of salaries
Query: Compare sales by region
Query: Show correlation between height and weight
Query: What are the top 10 products by sales?
```

#### Single Query Mode

Process a single query without entering interactive mode:

```bash
python main.py your_data.csv --query "What is the mean income?"
```

### Database Mode

#### Connecting to MySQL Database

Connect to a MySQL database using command-line arguments:

```bash
python main.py --db-host localhost --db-user root --db-password yourpassword --db-name mydatabase
```

Or let the tool prompt for password:

```bash
python main.py --db-host localhost --db-user root --db-name mydatabase
# Password will be prompted securely
```

#### Database Query Examples

Once connected, ask questions about your database:

```
Query: What is the average salary in the employees table?
Query: Show me the distribution of sales by region
Query: Compare revenue by department
Query: What are the top 10 customers by total orders?
```

The tool will:
1. **Generate and display the SQL query** that will be executed
2. **Execute the query** and retrieve results
3. **Analyze the results** and generate visualizations
4. **Suggest interesting questions** you might want to ask next

#### Special Commands in Database Mode

- `summary` - Show database schema summary
- `suggestions` - Show suggested questions based on database structure
- `exit` or `quit` or `q` - Exit the program

### Custom Output Directory

Specify where to save visualizations:

```bash
python main.py your_data.csv --output my_charts/
python main.py --db-host localhost --db-user root --db-name mydb --output my_charts/
```

## Supported Query Types

The tool can handle various types of questions:

1. **Statistics**: "What is the average age?", "Show me the median income"
2. **Distributions**: "Show the distribution of salaries", "Plot a histogram of ages"
3. **Comparisons**: "Compare sales by region", "Show revenue by department"
4. **Correlations**: "What's the correlation between height and weight?"
5. **Trends**: "Show trends over time", "How did sales change over time?"
6. **Aggregations**: "What are the top 10 products by sales?", "Group by category and show totals"
7. **Filtering**: "Show only records where age is greater than 30"

## Supported Data Formats

### File Formats

- CSV (`.csv`)
- JSON (`.json`)
- Excel (`.xlsx`, `.xls`)
- Parquet (`.parquet`)
- Feather (`.feather`)

### Database Systems

- MySQL (via pymysql)

## Examples

### File Mode Examples

#### Example 1: Statistical Analysis

```bash
python main.py sales_data.csv --query "What is the average revenue?"
```

#### Example 2: Distribution Analysis

```bash
python main.py employee_data.csv --query "Show me the distribution of salaries"
```

#### Example 3: Grouped Analysis

```bash
python main.py sales_data.csv --query "Compare total sales by region"
```

#### Example 4: Trend Analysis

```bash
python main.py time_series_data.csv --query "Show trends over time"
```

### Database Mode Examples

#### Example 1: Connect and Query

```bash
# Connect to database
python main.py --db-host localhost --db-user root --db-password pass123 --db-name company_db

# Then in interactive mode:
Query: What is the average salary in the employees table?
# Tool displays: SELECT AVG(`salary`) as avg_salary FROM `employees`
# Tool executes query and shows results with visualization
# Tool suggests related questions
```

#### Example 2: Single Database Query

```bash
python main.py --db-host localhost --db-user root --db-name company_db --query "Show top 10 products by sales"
```

#### Example 3: Database with Custom Port

```bash
python main.py --db-host localhost --db-port 3307 --db-user root --db-name mydb
```

## Architecture

The tool is organized into modular components:

### Core Modules

- **`data_loader.py`**: Handles loading datasets from various file formats and database connections
- **`query_analyzer.py`**: Analyzes natural language queries to extract intent and parameters
- **`data_analyzer.py`**: Performs data analysis operations based on query intent
- **`visualizer.py`**: Generates visualizations from analysis results
- **`main.py`**: Main entry point and orchestration

### Database-Specific Modules

- **`db_connection.py`**: Handles MySQL database connections and SQL query execution
- **`sql_query_generator.py`**: Converts natural language queries into SQL queries
- **`question_suggester.py`**: Analyzes database schema and suggests interesting questions

## Features in Detail

### SQL Query Display

When using database mode, the tool displays the SQL query it generates before executing it. This allows you to:
- Verify that the query matches your intent
- Learn SQL by seeing how natural language is translated
- Debug query generation issues
- Copy and modify queries for advanced use cases

### Question Suggestions

The tool analyzes your database schema and automatically suggests interesting questions you might want to ask. Suggestions are based on:
- Column types (numeric, categorical, date)
- Table relationships
- Common analysis patterns (statistics, distributions, comparisons, trends)
- Cross-table relationships

Type `suggestions` in interactive mode to see suggested questions, or suggestions are automatically shown after each query in database mode.

## Limitations

- Natural language parsing uses pattern matching, which may not handle all query variations
- Column name detection relies on exact matches or partial word matching
- Complex queries with multiple conditions may need refinement
- SQL generation supports basic SELECT queries with aggregations, GROUP BY, ORDER BY, and LIMIT
- JOIN queries are generated based on common column names (foreign key relationships should be explicit)
- For advanced queries, consider using an LLM-based query analyzer (can be extended)

## Extending the Tool

The tool is designed to be extensible:

1. **Add new query patterns**: Edit `query_analyzer.py` to add new intent detection patterns
2. **Add new visualizations**: Extend `visualizer.py` with new chart types
3. **Add new analysis types**: Add methods to `data_analyzer.py` for new analysis operations
4. **Integrate LLM**: Replace or augment `QueryAnalyzer` with an LLM-based query understanding system

## License

This project is provided as-is for educational and personal use.

