
import frappe
from finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page import NextJSPage

def test_route_generation():
    print("Starting Route Generation Tests...")
    
    # 1. Test automatic generation when empty
    doc1 = frappe.new_doc("NextJS Page")
    doc1.title = "Test Page One"
    doc1.insert()
    print(f"Test 1: Page '{doc1.title}' created with route: {doc1.route}")
    assert doc1.route == "/test-page-one", f"Expected /test-page-one, got {doc1.route}"
    
    # 2. Test preservation when manual route set
    doc2 = frappe.new_doc("NextJS Page")
    doc2.title = "Test Page Two"
    doc2.route = "/manual-route"
    doc2.insert()
    print(f"Test 2: Page '{doc2.title}' created with manual route: {doc2.route}")
    assert doc2.route == "/manual-route", f"Expected /manual-route, got {doc2.route}"
    
    # 3. Test preservation after title update
    doc2.title = "Updated Test Page Two"
    doc2.save()
    print(f"Test 3: Page '{doc2.title}' updated, route remains: {doc2.route}")
    assert doc2.route == "/manual-route", f"Expected /manual-route after update, got {doc2.route}"
    
    # Clean up
    doc1.delete()
    doc2.delete()
    frappe.db.commit()
    print("Tests passed successfully!")

if __name__ == "__main__":
    test_route_generation()
