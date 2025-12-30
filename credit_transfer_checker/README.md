# PHCC Credit Transfer Checker

A Python application designed specifically for **Patrick & Henry Community College (PHCC)** students in Martinsville, VA to check if their credits will transfer to other colleges and universities.

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
1. **Check Credit Transfers**: Enter your PHCC courses and see if they transfer to your target college
2. **Add Transfer Equivalency**: Add new transfer mappings to the database
3. **View Equivalencies**: See all available transfer equivalencies in the database
4. **Exit**: Close the application

### Example Usage

1. Start the application:
   ```bash
   python credit_transfer.py
   ```

2. Select option 1 to check transfers

3. Enter your target college (e.g., "Virginia Tech", "University of Virginia", "James Madison University")

4. Enter your PHCC courses one by one:
   - Course Code: ENG 111
   - Course Name: College Composition I
   - Credits: 3
   - Grade: A
   - (College is automatically set to Patrick & Henry Community College)

5. View the results showing which courses transfer and how

## Data Storage

Transfer equivalencies are stored in `transfer_equivalencies.json`. The file is automatically created with sample data on first run.

### Sample Data Structure

The application comes with pre-loaded transfer equivalencies from PHCC to major Virginia universities including:
- **Virginia Tech** - Engineering, sciences, and general education courses
- **University of Virginia** - Core curriculum courses
- **James Madison University** - General education and major prerequisites
- **Radford University** - Transfer pathways
- **Virginia Commonwealth University** - Various programs
- **Old Dominion University** - Transfer agreements

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
- Enter multiple PHCC courses from your transcript
- Courses are automatically associated with Patrick & Henry Community College
- Check if each course has a transfer equivalency
- See how PHCC courses map to the target college's course codes
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

## Common PHCC Transfer Destinations

The database includes equivalencies for:
- Virginia Tech (VT)
- University of Virginia (UVA)
- James Madison University (JMU)
- Radford University
- Virginia Commonwealth University (VCU)
- Old Dominion University (ODU)

More equivalencies can be added through the application interface.

## Future Enhancements

Potential improvements:
- Web interface
- Integration with PHCC and Virginia college databases
- GPA calculation for transfer credits
- Export results to PDF
- Search and filter capabilities
- Support for multiple target colleges at once
- Integration with Virginia's Transfer Virginia initiative

## License

This project is open source and available for educational use.

## Contributing

Feel free to add more transfer equivalencies or improve the functionality!

