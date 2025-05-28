# *******************************************************************************************************************************
#
#   Project Name        : Book suggestion app
#   Project Purpose     : IC Leaf Final Capstone Project
#   Author              : Sreeja R
#   Revistion History   : 1.0
#   Modification        : Initial Version
#   Created Date        : 28 May 2025    
#   Summary             : This is a desktop GUI application built with PyQt5 that helps users discover books by fetching data
#                         from the Google Books API and providing filtering and random suggestion capabilities.
# *******************************************************************************************************************************


# *********************************************************************************************************
# Imports
# *********************************************************************************************************
import sys                                                                            # System library imported
import random                                                                         # To pich the random book suggestion
import requests                                                                       # This is used fir API call
import pandas as pd                                                                   # pandas library                    
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,         # For GUI creation
                             QHBoxLayout, QComboBox, QLineEdit, QPushButton, 
                             QTextEdit, QLabel, QMessageBox)

# *********************************************************************************************************
# Function Name : fetch_books
# Purpose       : Retrieves book data from Google Books API for a specified genre/subject
# Parameter     : 1. subject: The book genre/category to search  
#                 2. max_results: Maximum number of books to retrieve (default: 40)
# Return        : df: pandas DataFrame with columns: Title, Authors, Genre, Publication Year, Ratings
# *********************************************************************************************************
def fetch_books(subject, max_results=40):
    #-----------------------------   
    #Data Collection
    #-----------------------------   
    # Error Handling 
    try:                                                                               
        # Construct API URL (search by subject=genre)
        # Google Books API
        url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{subject}&maxResults={max_results}"   
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:                                  
        raise RuntimeError(f"API request failed: {e}")

    items = data.get('items', [])
    # store data in list
    books = []                                                                         
    for item in items:
        info = item.get('volumeInfo', {})
        # Extract fields with defaults
        title = info.get('title', 'Unknown Title')
        authors = ", ".join(info.get('authors', ['Unknown Author']))
        published = info.get('publishedDate', '')
        # Try to extract year
        year = None
        if published:
            year = published.split("-")[0]
            if year.isdigit():
                year = int(year)
            else:
                year = None
        categories = ", ".join(info.get('categories', ['Uncategorized']))
        ratings = info.get('ratingsCount', 0)
        books.append({
            'Title': title,
            'Authors': authors,
            'Genre': categories,
            'Publication Year': year if year else 0,
            'Ratings': ratings
        })
    #-----------------------------    
    #Data Processing
    #-----------------------------   
    # Create DataFrame and clean data
    df = pd.DataFrame(books)
    # Drop duplicates and rows without a title
    df.drop_duplicates(subset=['Title','Authors'], inplace=True)
    df = df[df['Title'] != 'Unknown Title']
    # Data cleaning: Fill missing years, rating with 0, ensure int type
    df['Publication Year'] = pd.to_numeric(df['Publication Year'], errors='coerce').fillna(0).astype(int)
    df['Ratings'] = pd.to_numeric(df['Ratings'], errors='coerce').fillna(0).astype(int)
    return df
# *********************************************************************************************************


# *********************************************************************************************************
# Class Name    : MainWindow
# Purpose       : Main GUI window class that provides the user interface for book filtering and suggestions
# Methods       : init_ui, apply_filter, suggest_random
# *********************************************************************************************************

class MainWindow(QMainWindow):
    # constructor: it get invoke during object creation
    def __init__(self, df):                                                       
        super().__init__() 
        # The pandas DataFrame of books
        self.df = df                                                             
        self.init_ui()
        
# *********************************************************************************
# Function Name : init_ui
# Purpose       : Creates and configures the graphical user interface
# Parameter     : N/A
# Return        : N/A
# *********************************************************************************   
    def init_ui(self):
        self.setWindowTitle("Book Suggestion App")
        self.resize(1000, 1000)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Top controls: Genre dropdown and filters
        controls = QHBoxLayout()
        layout.addLayout(controls)

        controls.addWidget(QLabel("Genre:"))
        self.combo_genre = QComboBox()
        genres = sorted(set(self.df['Genre'].str.split(', ').str[0].tolist()))
        self.combo_genre.addItems(genres)
        controls.addWidget(self.combo_genre)

        controls.addWidget(QLabel("Min Year:"))
        self.input_year = QLineEdit()
        self.input_year.setPlaceholderText("2000 to 2025")
        controls.addWidget(self.input_year)

        controls.addWidget(QLabel("Min Ratings:"))
        self.input_ratings = QLineEdit()
        self.input_ratings.setPlaceholderText("1 to 10")
        controls.addWidget(self.input_ratings)

        self.btn_filter = QPushButton("Filter")
        self.btn_filter.clicked.connect(self.apply_filter)
        controls.addWidget(self.btn_filter)

        self.btn_random = QPushButton("Suggest Random")
        self.btn_random.clicked.connect(self.suggest_random)
        controls.addWidget(self.btn_random)

        # Text area for results/details
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
# *********************************************************************************
# Function Name : apply_filter
# Purpose       : Filters the book dataset based on user-selected criteria and 
#                 displays matching books
# Parameter     : N/A
# Return        : N/A
# ********************************************************************************* 

    def apply_filter(self):
        genre = self.combo_genre.currentText()
        year_text = self.input_year.text().strip()
        ratings_text = self.input_ratings.text().strip()
        # Error Handling
        try:                                                                         
            min_year = int(year_text) if year_text else 0
        except ValueError:                                                          
            QMessageBox.warning(self, "Input Error", "Year must be an integer.")
            return
        try:                                                                         
            min_ratings = int(ratings_text) if ratings_text else 0
        except ValueError:                                                           
            QMessageBox.warning(self, "Input Error", "Ratings must be an integer.")
            return

        # Filter the dataframe
        df_filtered = self.df.copy()
        if genre:
            # filter genre column for containing the selected genre
            df_filtered = df_filtered[df_filtered['Genre'].str.contains(genre, case=False, na=False)]
        df_filtered = df_filtered[(df_filtered['Publication Year'] >= min_year) & 
                                  (df_filtered['Ratings'] >= min_ratings)]
        if df_filtered.empty:
            self.text_area.setText("No books found with these filters.")
            return
        # Display titles of filtered books
        titles = df_filtered['Title'] + " by " + df_filtered['Authors']
        self.text_area.setText("\n".join(titles.tolist()))
        
# *********************************************************************************
# Function Name : suggest_random
# Purpose       : Selects and displays a random book from the filtered dataset
#                 with complete details
# Parameter     : N/A
# Return        : N/A
# ********************************************************************************* 

    def suggest_random(self):
        genre = self.combo_genre.currentText()
        year_text = self.input_year.text().strip()
        ratings_text = self.input_ratings.text().strip()
        # Error Handling
        try:                                                                        
            min_year = int(year_text) if year_text else 0
            min_ratings = int(ratings_text) if ratings_text else 0
        except ValueError:                                                          
            # Handled similarly as in apply_filter
            QMessageBox.warning(self, "Input Error", "Year and Ratings must be integers.")
            return

        df_filtered = self.df.copy()
        if genre:
            df_filtered = df_filtered[df_filtered['Genre'].str.contains(genre, case=False, na=False)]
        df_filtered = df_filtered[(df_filtered['Publication Year'] >= min_year) & 
                                  (df_filtered['Ratings'] >= min_ratings)]
        if df_filtered.empty:
            QMessageBox.information(self, "No Books", "No books match the criteria.")
            return
        # Pick random row
        book = df_filtered.sample(1).iloc[0]
        details = (f"Title: {book['Title']}\n"
                   f"Authors: {book['Authors']}\n"
                   f"Genre: {book['Genre']}\n"
                   f"Published Year: {book['Publication Year']}\n"
                   f"Ratings Count: {book['Ratings']}")
        self.text_area.setText(details)
# *********************************************************************************************************
        
        
# *********************************************************************************************************
# Function Name : main
# Purpose       : Application entry point that initializes data and launches the GUI
# Parameter     : N/A
# Return        : N/A
# *********************************************************************************************************

if __name__ == "__main__":                                                            
    # Example usage: fetch data for a couple of genres and launch GUI
    # Error Handling
    try:                                                                              
        # Fetch books for a couple of genres (this could be expanded or made dynamic)
        df_fiction = fetch_books("Fiction")
        df_history = fetch_books("History")
        # using pandas lib we concatenate genre
        df_all = pd.concat([df_fiction, df_history], ignore_index=True)   
        # store locally if needed enable the below line it is stored locally      
        # df_all.to_csv("books.csv", index=False)       
    except RuntimeError as e:                                                        
        QMessageBox.critical(None, "API Error", str(e))
        # To close the window using system exit function
        sys.exit(1)                                                                   

    # Cleaning the DataFrame
    # Removing Duplicate if any
    df_all.drop_duplicates(subset=['Title','Authors'], inplace=True)                  

    app = QApplication(sys.argv)
    # Error Handling
    try:                                                                              
        window = MainWindow(df_all)
        # Show helps to dipsplay the ouput window
        window.show()                                                                 
        sys.exit(app.exec_())
    except Exception as e:                                                            
        QMessageBox.critical(None, "Application Error", str(e))
        sys.exit(1)
# *********************************************************************************************************
# End of the Program
# *********************************************************************************************************
