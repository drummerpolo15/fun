#!/usr/bin/env python3
"""
PHCC Credit Transfer Checker
Allows Patrick and Henry Community College (PHCC) students to check if their 
credits will transfer to other colleges and universities.
Patrick & Henry Community College - Martinsville, VA
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Course:
    """Represents a course taken at a college."""
    course_code: str
    course_name: str
    credits: float
    grade: str
    college: str


@dataclass
class TransferEquivalency:
    """Represents how a course transfers from one college to another."""
    source_college: str
    source_course_code: str
    target_college: str
    target_course_code: str
    target_course_name: str
    credits_transferred: float
    notes: str = ""


class CreditTransferChecker:
    """Main class for checking credit transfers."""
    
    def __init__(self, equivalency_file: str = "transfer_equivalencies.json"):
        """Initialize the checker with a database file."""
        self.equivalency_file = equivalency_file
        self.equivalencies: List[TransferEquivalency] = []
        self.load_equivalencies()
    
    def load_equivalencies(self):
        """Load transfer equivalencies from JSON file."""
        if os.path.exists(self.equivalency_file):
            try:
                with open(self.equivalency_file, 'r') as f:
                    data = json.load(f)
                    self.equivalencies = [
                        TransferEquivalency(**eq) for eq in data
                    ]
            except Exception as e:
                print(f"Warning: Could not load equivalencies: {e}")
                self.equivalencies = []
        else:
            # Create default sample data
            self._create_sample_data()
            self.save_equivalencies()
    
    def save_equivalencies(self):
        """Save transfer equivalencies to JSON file."""
        try:
            with open(self.equivalency_file, 'w') as f:
                json.dump(
                    [asdict(eq) for eq in self.equivalencies],
                    f,
                    indent=2
                )
        except Exception as e:
            print(f"Error saving equivalencies: {e}")
    
    def _create_sample_data(self):
        """Create PHCC transfer equivalency data for common Virginia universities."""
        phcc = "Patrick & Henry Community College"
        
        sample_data = [
            # PHCC to Virginia Tech
            TransferEquivalency(
                source_college=phcc,
                source_course_code="ENG 111",
                target_college="Virginia Tech",
                target_course_code="ENGL 1105",
                target_course_name="First-Year Writing",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="MTH 173",
                target_college="Virginia Tech",
                target_course_code="MATH 1225",
                target_course_name="Calculus of a Single Variable",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="BIO 101",
                target_college="Virginia Tech",
                target_course_code="BIOL 1105",
                target_course_name="Principles of Biology",
                credits_transferred=4.0,
                notes="Direct equivalent, includes lab"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="CHM 111",
                target_college="Virginia Tech",
                target_course_code="CHEM 1035",
                target_course_name="General Chemistry",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="HIS 121",
                target_college="Virginia Tech",
                target_course_code="HIST 1115",
                target_course_name="United States History",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            
            # PHCC to University of Virginia
            TransferEquivalency(
                source_college=phcc,
                source_course_code="ENG 111",
                target_college="University of Virginia",
                target_course_code="ENWR 1510",
                target_course_name="Academic Writing",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="MTH 173",
                target_college="University of Virginia",
                target_course_code="MATH 1310",
                target_course_name="Calculus I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="BIO 101",
                target_college="University of Virginia",
                target_course_code="BIOL 2100",
                target_course_name="Introduction to Biology",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            
            # PHCC to James Madison University
            TransferEquivalency(
                source_college=phcc,
                source_course_code="ENG 111",
                target_college="James Madison University",
                target_course_code="WRIT 101",
                target_course_name="Critical Reading and Writing",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="MTH 173",
                target_college="James Madison University",
                target_course_code="MATH 235",
                target_course_name="Calculus I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="BIO 101",
                target_college="James Madison University",
                target_course_code="BIO 140",
                target_course_name="Foundations of Biology I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="PSY 200",
                target_college="James Madison University",
                target_course_code="PSYC 101",
                target_course_name="General Psychology",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            
            # PHCC to Radford University
            TransferEquivalency(
                source_college=phcc,
                source_course_code="ENG 111",
                target_college="Radford University",
                target_course_code="ENGL 111",
                target_course_name="Composition I",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="MTH 173",
                target_college="Radford University",
                target_course_code="MATH 151",
                target_course_name="Calculus I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="BIO 101",
                target_college="Radford University",
                target_course_code="BIOL 131",
                target_course_name="General Biology I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            
            # PHCC to Virginia Commonwealth University
            TransferEquivalency(
                source_college=phcc,
                source_course_code="ENG 111",
                target_college="Virginia Commonwealth University",
                target_course_code="UNIV 111",
                target_course_name="Focus Inquiry",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="MTH 173",
                target_college="Virginia Commonwealth University",
                target_course_code="MATH 200",
                target_course_name="Calculus with Analytic Geometry I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="BIO 101",
                target_college="Virginia Commonwealth University",
                target_course_code="BIOL 151",
                target_course_name="Introduction to Biological Sciences I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            
            # PHCC to Old Dominion University
            TransferEquivalency(
                source_college=phcc,
                source_course_code="ENG 111",
                target_college="Old Dominion University",
                target_course_code="ENGL 110C",
                target_course_name="English Composition",
                credits_transferred=3.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="MTH 173",
                target_college="Old Dominion University",
                target_course_code="MATH 211",
                target_course_name="Calculus I",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
            TransferEquivalency(
                source_college=phcc,
                source_course_code="BIO 101",
                target_college="Old Dominion University",
                target_course_code="BIOL 110N",
                target_course_name="Principles of Biology",
                credits_transferred=4.0,
                notes="Direct equivalent"
            ),
        ]
        self.equivalencies = sample_data
    
    def check_transfer(self, course: Course, target_college: str) -> Optional[TransferEquivalency]:
        """Check if a course transfers to the target college."""
        for eq in self.equivalencies:
            if (eq.source_college == course.college and
                eq.source_course_code.upper() == course.course_code.upper() and
                eq.target_college == target_college):
                return eq
        return None
    
    def check_multiple_courses(self, courses: List[Course], target_college: str) -> Dict[str, Tuple[Optional[TransferEquivalency], Course]]:
        """Check transfer status for multiple courses."""
        results = {}
        for course in courses:
            transfer = self.check_transfer(course, target_college)
            results[course.course_code] = (transfer, course)
        return results
    
    def add_equivalency(self, equivalency: TransferEquivalency):
        """Add a new transfer equivalency."""
        self.equivalencies.append(equivalency)
        self.save_equivalencies()
    
    def get_total_transferable_credits(self, courses: List[Course], target_college: str) -> float:
        """Calculate total transferable credits."""
        total = 0.0
        for course in courses:
            transfer = self.check_transfer(course, target_college)
            if transfer:
                total += transfer.credits_transferred
        return total


def print_header():
    """Print a nice header."""
    print("\n" + "=" * 70)
    print(" " * 10 + "PHCC CREDIT TRANSFER CHECKER")
    print(" " * 5 + "Patrick & Henry Community College - Martinsville, VA")
    print("=" * 70 + "\n")


def print_results(results: Dict[str, Tuple[Optional[TransferEquivalency], Course]], target_college: str):
    """Print transfer check results in a formatted way."""
    print(f"\n{'='*60}")
    print(f"Transfer Results for: {target_college}")
    print(f"{'='*60}\n")
    
    transferable_count = 0
    total_credits = 0.0
    
    for course_code, (transfer, course) in results.items():
        print(f"Course: {course.course_code} - {course.course_name}")
        print(f"  Taken at: {course.college}")
        print(f"  Credits: {course.credits}")
        print(f"  Grade: {course.grade}")
        
        if transfer:
            print(f"  ✅ TRANSFERS AS:")
            print(f"     {transfer.target_course_code} - {transfer.target_course_name}")
            print(f"     Credits: {transfer.credits_transferred}")
            if transfer.notes:
                print(f"     Notes: {transfer.notes}")
            transferable_count += 1
            total_credits += transfer.credits_transferred
        else:
            print(f"  ❌ NO TRANSFER EQUIVALENCY FOUND")
            print(f"     This course may not transfer or equivalency not in database")
        
        print()
    
    print(f"{'='*60}")
    print(f"Summary:")
    print(f"  Transferable courses: {transferable_count} of {len(results)}")
    print(f"  Total transferable credits: {total_credits}")
    print(f"{'='*60}\n")


def get_course_input() -> Course:
    """Get course information from user."""
    print("\nEnter course information:")
    course_code = input("  Course Code (e.g., MATH 101): ").strip()
    course_name = input("  Course Name: ").strip()
    credits = float(input("  Credits: ").strip())
    grade = input("  Grade (e.g., A, B, C): ").strip().upper()
    college = input("  College/University where taken: ").strip()
    
    return Course(
        course_code=course_code,
        course_name=course_name,
        credits=credits,
        grade=grade,
        college=college
    )


def interactive_mode():
    """Run the interactive CLI mode."""
    checker = CreditTransferChecker()
    phcc = "Patrick & Henry Community College"
    
    print_header()
    print("Welcome, PHCC students! This tool helps you check if your")
    print("Patrick & Henry Community College credits will transfer to other institutions.")
    print("\nYou can:")
    print("  1. Check if your PHCC courses transfer to a target college")
    print("  2. Add new transfer equivalencies to the database")
    print("  3. View all available equivalencies")
    print("  4. Exit")
    
    while True:
        print("\n" + "-" * 60)
        choice = input("\nWhat would you like to do? (1-4): ").strip()
        
        if choice == "1":
            # Check transfers
            print("\n--- Check Credit Transfers ---")
            print("\nCommon transfer destinations:")
            print("  - Virginia Tech")
            print("  - University of Virginia")
            print("  - James Madison University")
            print("  - Radford University")
            print("  - Virginia Commonwealth University")
            print("  - Old Dominion University")
            print("  - (or enter any other college/university)")
            target_college = input("\nEnter target college/university: ").strip()
            
            courses = []
            print(f"\nEnter your PHCC courses (press Enter with empty course code to finish):")
            print("Note: Courses are assumed to be from Patrick & Henry Community College")
            while True:
                course_code = input("\nPHCC Course Code (e.g., ENG 111, MTH 173) or press Enter to finish: ").strip()
                if not course_code:
                    break
                
                # Try to find course in database or get full info
                course_name = input("  Course Name: ").strip()
                credits = float(input("  Credits: ").strip())
                grade = input("  Grade: ").strip().upper()
                
                # Auto-fill PHCC as the college
                courses.append(Course(
                    course_code=course_code,
                    course_name=course_name,
                    credits=credits,
                    grade=grade,
                    college=phcc
                ))
            
            if courses:
                results = checker.check_multiple_courses(courses, target_college)
                print_results(results, target_college)
            else:
                print("No courses entered.")
        
        elif choice == "2":
            # Add equivalency
            print("\n--- Add Transfer Equivalency ---")
            print("Source college will be set to Patrick & Henry Community College")
            source_college = phcc
            source_course = input("PHCC Course Code (e.g., ENG 111): ").strip()
            target_college = input("Target College/University: ").strip()
            target_course = input("Target Course Code: ").strip()
            target_course_name = input("Target Course Name: ").strip()
            credits = float(input("Credits Transferred: ").strip())
            notes = input("Notes (optional): ").strip()
            
            equivalency = TransferEquivalency(
                source_college=source_college,
                source_course_code=source_course,
                target_college=target_college,
                target_course_code=target_course,
                target_course_name=target_course_name,
                credits_transferred=credits,
                notes=notes
            )
            
            checker.add_equivalency(equivalency)
            print(f"\n✅ Equivalency added successfully!")
        
        elif choice == "3":
            # View equivalencies
            print("\n--- Available PHCC Transfer Equivalencies ---")
            if checker.equivalencies:
                # Group by target college
                by_college = {}
                for eq in checker.equivalencies:
                    if eq.target_college not in by_college:
                        by_college[eq.target_college] = []
                    by_college[eq.target_college].append(eq)
                
                for college, eqs in sorted(by_college.items()):
                    print(f"\n{'='*70}")
                    print(f"  {college}")
                    print(f"{'='*70}")
                    for eq in eqs:
                        print(f"  PHCC {eq.source_course_code} → {eq.target_course_code} ({eq.target_course_name})")
                        print(f"    Credits: {eq.credits_transferred}")
                        if eq.notes:
                            print(f"    Notes: {eq.notes}")
            else:
                print("No equivalencies in database.")
        
        elif choice == "4":
            print("\nThank you for using PHCC Credit Transfer Checker!")
            print("Good luck with your transfer!")
            break
        
        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

