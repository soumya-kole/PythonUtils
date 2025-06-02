import json
import html
from typing import List, Dict, Any, Optional


class BeautifulTableGenerator:
    def __init__(self,
                 header_color: str = "#2c3e50",
                 header_text_color: str = "#ffffff",
                 even_row_color: str = "#f8f9fa",
                 odd_row_color: str = "#ffffff",
                 border_color: str = "#dee2e6",
                 hover_color: str = "#e3f2fd"):
        """
        Initialize the table generator with customizable colors.

        Args:
            header_color: Background color for header row
            header_text_color: Text color for header
            even_row_color: Background color for even rows
            odd_row_color: Background color for odd rows
            border_color: Border color for table
            hover_color: Hover effect color
        """
        self.header_color = header_color
        self.header_text_color = header_text_color
        self.even_row_color = even_row_color
        self.odd_row_color = odd_row_color
        self.border_color = border_color
        self.hover_color = hover_color

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return html.escape(str(text))

    def _generate_css(self) -> str:
        """Generate CSS styles for the table."""
        return f"""
        <style>
            .beautiful-table {{
                border-collapse: collapse;
                margin: 20px auto;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                overflow: hidden;
                width: auto;
                min-width: 300px;
            }}

            .beautiful-table th {{
                background-color: {self.header_color};
                color: {self.header_text_color};
                font-weight: 600;
                padding: 12px 16px;
                text-align: left;
                font-size: 14px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                border: none;
                white-space: nowrap;
            }}

            .beautiful-table td {{
                padding: 10px 16px;
                border-bottom: 1px solid {self.border_color};
                font-size: 14px;
                line-height: 1.4;
                word-wrap: break-word;
                max-width: 300px;
            }}

            .beautiful-table tr:nth-child(even) {{
                background-color: {self.even_row_color};
            }}

            .beautiful-table tr:nth-child(odd) {{
                background-color: {self.odd_row_color};
            }}

            .beautiful-table tr:hover {{
                background-color: {self.hover_color} !important;
                transition: background-color 0.2s ease;
            }}

            .beautiful-table tr:last-child td {{
                border-bottom: none;
            }}

            .table-container {{
                overflow-x: auto;
                margin: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }}

            .table-title {{
                text-align: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: {self.header_color};
                margin-bottom: 10px;
                font-size: 24px;
                font-weight: 300;
            }}
        </style>
        """

    def json_to_html_table(self,
                           json_data: List[Dict[str, Any]],
                           title: Optional[str] = None,
                           custom_headers: Optional[List[str]] = None) -> str:
        """
        Convert JSON data to a beautiful HTML table.

        Args:
            json_data: List of dictionaries containing table data
            title: Optional title for the table
            custom_headers: Optional custom header names

        Returns:
            Complete HTML string with embedded CSS
        """
        if not json_data:
            return "<p>No data provided</p>"

        # Get all unique keys from all dictionaries to handle varying columns
        all_keys = set()
        for item in json_data:
            all_keys.update(item.keys())

        # Sort keys for consistent column order
        columns = sorted(list(all_keys))

        # Use custom headers if provided
        if custom_headers:
            if len(custom_headers) != len(columns):
                raise ValueError("Number of custom headers must match number of columns")
            headers = custom_headers
        else:
            # Format column names (replace underscores, capitalize)
            headers = [col.replace('_', ' ').title() for col in columns]

        # Start building HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Beautiful Data Table</title>
            {self._generate_css()}
        </head>
        <body>
        """

        if title:
            html_content += f'<h2 class="table-title">{self._escape_html(title)}</h2>'

        html_content += """
        <div class="table-container">
            <table class="beautiful-table">
                <thead>
                    <tr>
        """

        # Add headers
        for header in headers:
            html_content += f'<th>{self._escape_html(header)}</th>'

        html_content += """
                    </tr>
                </thead>
                <tbody>
        """

        # Add data rows
        for row_data in json_data:
            html_content += '<tr>'
            for col in columns:
                cell_value = row_data.get(col, '')
                # Handle different data types
                if isinstance(cell_value, (list, dict)):
                    cell_value = json.dumps(cell_value, indent=2)
                html_content += f'<td>{self._escape_html(cell_value)}</td>'
            html_content += '</tr>'

        html_content += """
                </tbody>
            </table>
        </div>
        </body>
        </html>
        """

        return html_content

    def save_table(self, json_data: List[Dict[str, Any]],
                   filename: str = "table.html",
                   title: Optional[str] = None,
                   custom_headers: Optional[List[str]] = None):
        """Save the HTML table to a file."""
        html_content = self.json_to_html_table(json_data, title, custom_headers)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Table saved as {filename}")


# Example usage and demonstration
def demo():
    """Demonstrate the table generator with sample data."""

    # Sample JSON data with varying columns
    sample_data = [
        {"name": "John Doe", "age": 30, "city": "New York", "salary": 75000, "department": "Engineering"},
        {"name": "Jane Smith", "age": 25, "city": "San Francisco", "salary": 85000, "department": "Design"},
        {"name": "Bob Johnson", "age": 35, "city": "Chicago", "salary": 65000, "department": "Marketing",
         "bonus": 5000},
        {"name": "Alice Brown", "age": 28, "city": "Boston", "salary": 70000, "department": "Engineering"},
        {"name": "Charlie Wilson", "age": 32, "city": "Seattle", "salary": 90000, "department": "Engineering",
         "remote": True}
    ]

    # Create table generator with default colors
    generator = BeautifulTableGenerator()

    # Generate and save basic table
    generator.save_table(sample_data, "employee_table.html", "Employee Information")

    # Create another generator with custom colors
    custom_generator = BeautifulTableGenerator(
        header_color="#8e44ad",
        header_text_color="#ffffff",
        even_row_color="#f4f1fb",
        odd_row_color="#ffffff",
        hover_color="#e8d5f2"
    )

    # Sample data for different scenario
    product_data = [
        {"product_id": "P001", "product_name": "Laptop", "price": 999.99, "stock": 50, "category": "Electronics"},
        {"product_id": "P002", "product_name": "Smartphone", "price": 699.99, "stock": 100, "category": "Electronics"},
        {"product_id": "P003", "product_name": "Desk Chair", "price": 199.99, "stock": 25, "category": "Furniture"},
        {"product_id": "P004", "product_name": "Coffee Maker", "price": 89.99, "stock": 75, "category": "Appliances"}
    ]

    # Custom headers
    custom_headers = ["ID", "Product Name", "Price ($)", "In Stock", "Category"]

    custom_generator.save_table(
        product_data,
        "product_catalog.html",
        "Product Catalog",
        custom_headers
    )

    print("Demo completed! Check the generated HTML files.")


if __name__ == "__main__":
    my_data = [
        {"column1": "value1", "column2": "value2"},
        {"column1": "value3", "column2": "value4"}
    ]

    # Create generator
    generator = BeautifulTableGenerator(
        header_color="#34495e",
        even_row_color="#ecf0f1"
    )

    # Generate table
    html_table = generator.json_to_html_table(my_data, title="My Data Table")

    # Or save directly to file
    generator.save_table(my_data, "my_table.html", "My Data Table")
