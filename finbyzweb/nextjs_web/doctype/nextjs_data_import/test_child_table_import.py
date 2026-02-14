# Test script for NextJS Data Import with child tables
import frappe
import csv
import os

def create_test_csv_with_child_tables():
	"""Create a test CSV file with child table data"""
	
	# Sample data with child tables (FAQs and Related Links)
	data = [
		# Headers
		['Title', 'Route', 'Published', 'SEO title', 'Keywords', 'Small Description', 'Image', 'Main Section (HTML)', 'Content Type', 'Question (FAQs)', 'Answer (FAQs)', 'idx (FAQs)', 'Title (Related Links)', 'Route (Related Links)', 'idx (Related Links)'],
		# Row 1 - First document with first FAQ
		['Test Page 1', '/test-page-1', '1', 'Test SEO Title', 'test, keywords', 'Test description', '', '<p>Test Content</p>', 'HTML', 'What is this?', 'This is a test FAQ', '1', 'Home', '/', '1'],
		# Row 2 - Same document with second FAQ
		['Test Page 1', '/test-page-1', '1', 'Test SEO Title', 'test, keywords', 'Test description', '', '<p>Test Content</p>', 'HTML', 'How to use?', 'Just follow the instructions', '2', '', '', ''],
		# Row 3 - Same document with second related link
		['Test Page 1', '/test-page-1', '1', 'Test SEO Title', 'test, keywords', 'Test description', '', '<p>Test Content</p>', 'HTML', '', '', '', 'About', '/about', '2'],
	]
	
	# Write to CSV
	csv_path = '/tmp/test_nextjs_import.csv'
	with open(csv_path, 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerows(data)
	
	print(f"Created test CSV at: {csv_path}")
	return csv_path

def test_import():
	"""Test the import functionality"""
	
	# Create test CSV
	csv_path = create_test_csv_with_child_tables()
	
	# Upload the file
	with open(csv_path, 'rb') as f:
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "test_nextjs_import.csv",
			"content": f.read(),
			"is_private": 1
		})
		file_doc.insert()
	
	# Create import document
	import_doc = frappe.get_doc({
		"doctype": "NextJS Data Import",
		"import_file": file_doc.file_url,
		"source_doctype": "Web Page",
		"import_type": "Insert New"
	})
	import_doc.insert()
	
	print(f"Created import document: {import_doc.name}")
	
	# Run import
	try:
		import_doc.import_data()
		print("Import successful!")
		print(f"Log: {import_doc.log}")
		
		# Check if page was created
		if frappe.db.exists("NextJS Page", {"route": "/test-page-1"}):
			page = frappe.get_doc("NextJS Page", {"route": "/test-page-1"})
			print(f"\nPage created: {page.name}")
			print(f"Title: {page.title}")
			print(f"FAQs count: {len(page.faqs)}")
			print(f"Related pages count: {len(page.nextjs_related_page)}")
			
			if page.faqs:
				print("\nFAQs:")
				for faq in page.faqs:
					print(f"  - Q: {faq.question}")
					print(f"    A: {faq.answer}")
			
			if page.nextjs_related_page:
				print("\nRelated Pages:")
				for rel in page.nextjs_related_page:
					print(f"  - {rel.title} ({rel.route})")
		else:
			print("ERROR: Page was not created!")
			
	except Exception as e:
		print(f"Import failed: {str(e)}")
		import traceback
		traceback.print_exc()
	
	# Cleanup
	os.remove(csv_path)

if __name__ == "__main__":
	test_import()
