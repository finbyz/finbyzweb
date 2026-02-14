#!/usr/bin/env python3
"""
Script to update image URLs from finbyz.tech to erp.finbyz.tech in NextJS Page doctype.
Run this from bench console: bench --site <your-site> console
Then: from finbyzweb.nextjs_web.doctype.nextjs_page.update_image_urls import update_image_urls; update_image_urls()
"""

import frappe


def update_image_urls(dry_run=True):
	"""
	Update image URLs from finbyz.tech to erp.finbyz.tech.
	
	Args:
		dry_run (bool): If True, only shows what would be updated without making changes.
	"""
	
	# Get all NextJS Page documents
	pages = frappe.get_all("NextJS Page", fields=["name", "image", "navigation_image", "animated_image"])
	
	updated_count = 0
	fields_to_check = ["image", "navigation_image", "animated_image"]
	
	print(f"\n{'='*80}")
	print(f"Scanning {len(pages)} NextJS Pages for image URLs to update...")
	print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE UPDATE'}")
	print(f"{'='*80}\n")
	
	for page in pages:
		doc = frappe.get_doc("NextJS Page", page.name)
		changed = False
		changes = []
		
		for field in fields_to_check:
			old_value = doc.get(field)
			
			if old_value and "finbyz.tech" in old_value and not "erp.finbyz.tech" in old_value:
				# Update the URL
				new_value = old_value.replace("finbyz.tech", "erp.finbyz.tech")
				
				changes.append({
					"field": field,
					"old": old_value,
					"new": new_value
				})
				
				if not dry_run:
					doc.set(field, new_value)
				
				changed = True
		
		if changed:
			updated_count += 1
			print(f"Document: {doc.name} ({doc.title})")
			for change in changes:
				print(f"  Field: {change['field']}")
				print(f"    Old: {change['old']}")
				print(f"    New: {change['new']}")
			print()
			
			if not dry_run:
				# Save without validation to avoid triggering other hooks
				doc.save(ignore_permissions=True)
				frappe.db.commit()
	
	print(f"\n{'='*80}")
	if dry_run:
		print(f"DRY RUN COMPLETE: {updated_count} documents would be updated")
		print(f"Run with dry_run=False to make actual changes")
	else:
		print(f"UPDATE COMPLETE: {updated_count} documents updated successfully")
	print(f"{'='*80}\n")
	
	return updated_count


def update_specific_field(field_name="image", dry_run=True):
	"""
	Update URLs for a specific field only.
	
	Args:
		field_name (str): Field name to update (image, navigation_image, or animated_image)
		dry_run (bool): If True, only shows what would be updated without making changes.
	"""
	
	# Get all NextJS Page documents with the specific field
	pages = frappe.get_all("NextJS Page", fields=["name", field_name])
	
	updated_count = 0
	
	print(f"\n{'='*80}")
	print(f"Scanning field '{field_name}' in {len(pages)} NextJS Pages...")
	print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE UPDATE'}")
	print(f"{'='*80}\n")
	
	for page in pages:
		doc = frappe.get_doc("NextJS Page", page.name)
		old_value = doc.get(field_name)
		
		if old_value and "finbyz.tech" in old_value and not "erp.finbyz.tech" in old_value:
			new_value = old_value.replace("finbyz.tech", "erp.finbyz.tech")
			
			print(f"Document: {doc.name} ({doc.title})")
			print(f"  Old: {old_value}")
			print(f"  New: {new_value}")
			print()
			
			if not dry_run:
				doc.set(field_name, new_value)
				doc.save(ignore_permissions=True)
				frappe.db.commit()
			
			updated_count += 1
	
	print(f"\n{'='*80}")
	if dry_run:
		print(f"DRY RUN COMPLETE: {updated_count} documents would be updated")
		print(f"Run with dry_run=False to make actual changes")
	else:
		print(f"UPDATE COMPLETE: {updated_count} documents updated successfully")
	print(f"{'='*80}\n")
	
	return updated_count


if __name__ == "__main__":
	print("This script should be run from bench console")
	print("Example usage:")
	print("  bench --site <your-site> console")
	print("  from finbyzweb.nextjs_web.doctype.nextjs_page.update_image_urls import update_image_urls")
	print("  update_image_urls(dry_run=True)  # Preview changes")
	print("  update_image_urls(dry_run=False) # Apply changes")
