# Credit Transfer Checker

A Python application that helps students check if their college credits will transfer to another institution.

## Features

- ✅ Check if your courses transfer to a target college
- ✅ View transfer equivalencies and credit mappings
- ✅ Add new transfer equivalencies to the database
- ✅ Calculate total transferable credits
- ✅ Interactive command-line interface
- ✅ Persistent storage of transfer equivalencies (JSON)

## Requirements

- Python 3.7 or higher (uses dataclasses)
- No external dependencies required (uses only Python standard library)

## Installation

1. Navigate to the project directory:
   ```bash
   cd credit_transfer_checker
   ```

2. Make the script executable (optional):
   ```bash
   chmod +x credit_transfer.py
   ```

## Usage

### Interactive Mode

Run the application:
```bash
python credit_transfer.py
```

The interactive menu allows you to:
1. **Check Credit Transfers**: Enter your courses and see if they transfer to your target college
2. **Add Transfer Equivalency**: Add new transfer mappings to the database
3. **View Equivalencies**: See all available transfer equivalencies in the database
4. **Exit**: Close the application

### Example Usage

1. Start the application:
   ```bash
   python credit_transfer.py
   ```

2. Select option 1 to check transfers

3. Enter your target college (e.g., "State University")

4. Enter your courses one by one:
   - Course Code: MATH 101
   - Course Name: Calculus I
   - Credits: 3
   - Grade: A
   - College: Community College A

5. View the results showing which courses transfer and how

## Data Storage

Transfer equivalencies are stored in `transfer_equivalencies.json`. The file is automatically created with sample data on first run.

### Sample Data Structure

The application comes with sample transfer equivalencies including:
- Community College A → State University
- Community College B → State University

You can add your own equivalencies through the interactive menu.

## Project Structure

```
credit_transfer_checker/
├── credit_transfer.py          # Main application
├── requirements.txt             # Python requirements (none needed)
├── README.md                    # This file
└── transfer_equivalencies.json  # Transfer database (auto-created)
```

## Features in Detail

### Course Transfer Check
- Enter multiple courses from your transcript
- Check if each course has a transfer equivalency
- See how courses map to the target college's course codes
- View total transferable credits

### Adding Equivalencies
- Manually add new transfer mappings
- Include notes about special conditions
- Data is automatically saved to JSON file

### Data Model

**Course**: Represents a course taken at a college
- Course code, name, credits, grade, college

**TransferEquivalency**: Maps a course from one college to another
- Source college and course
- Target college and course
- Credits transferred
- Optional notes

## Future Enhancements

Potential improvements:
- Web interface
- Integration with college databases
- GPA calculation for transfer credits
- Export results to PDF
- Search and filter capabilities
- Support for multiple target colleges at once

## License

This project is open source and available for educational use.

## Contributing

Feel free to add more transfer equivalencies or improve the functionality!

