#!/usr/bin/env python
import os
import random
from time import sleep
from hubspot import HubSpot
from faker import Faker

# Imports for contacts creation
from hubspot.crm.contacts.models.simple_public_object_input import SimplePublicObjectInput
from hubspot.crm.contacts.models.batch_input_simple_public_object_batch_input import BatchInputSimplePublicObjectBatchInput
# Import for batch deletion (expects a list of objects with "id" keys)
from hubspot.crm.contacts.models.batch_input_simple_public_object_id import BatchInputSimplePublicObjectId

# Import for property creation
from hubspot.crm.properties.models.property_create import PropertyCreate

# Initialize Faker and the HubSpot client.
fake = Faker()
ACCESS_TOKEN = os.getenv("HUBSPOT_API_KEY", "YOUR_HUBSPOT_ACCESS_TOKEN")
client = HubSpot(access_token=ACCESS_TOKEN)

def delete_all_contacts():
    """
    Deletes all contacts in your HubSpot account.
    """
    print("Deleting all contacts...")
    all_ids = []
    after = None
    try:
        while True:
            page = client.crm.contacts.basic_api.get_page(limit=100, after=after, archived=False)
            if not hasattr(page, "results") or not page.results:
                break
            for contact in page.results:
                all_ids.append(contact.id)
            if page.paging and page.paging.next and hasattr(page.paging.next, "after"):
                after = page.paging.next.after
            else:
                break
    except Exception as e:
        print(f"Error retrieving contacts for deletion: {e}")
        return

    if all_ids:
        try:
            # Build the batch input for deletion.
            batch_input = BatchInputSimplePublicObjectId(
                inputs=[{"id": cid} for cid in all_ids]
            )
            # Pass the batch input as a positional argument.
            response = client.crm.contacts.batch_api.archive(batch_input)
            print(f"Deleted {len(all_ids)} contacts.")
        except Exception as e:
            print(f"Error deleting contacts: {e}")
    else:
        print("No contacts found to delete.")

def ensure_custom_property(object_type, property_name, label, prop_type, field_type, group_name="contactinformation"):
    """
    Checks if a custom property exists on the given object type; if not, creates it.
    """
    try:
        props_response = client.crm.properties.core_api.get_all(object_type=object_type)
    except Exception as e:
        print(f"Error retrieving properties for {object_type}: {e}")
        return

    existing = [prop.name for prop in props_response.results] if hasattr(props_response, "results") else []
    if property_name in existing:
        print(f"Property '{property_name}' already exists on {object_type}.")
        return

    property_create = PropertyCreate(
        name=property_name,
        label=label,
        type=prop_type,         # e.g., "string" or "number"
        field_type=field_type,   # e.g., "text" or "number"
        group_name=group_name
    )
    try:
        created = client.crm.properties.core_api.create(object_type=object_type, property_create=property_create)
        print(f"Created property '{property_name}' on {object_type}.")
    except Exception as e:
        print(f"Error creating property '{property_name}' on {object_type}: {e}")

def create_custom_properties_for_contacts():
    """
    Ensures that our custom properties exist on contacts.
    (For lead status we use the built-in hs_lead_status.)
    """
    object_type = "contacts"
    ensure_custom_property(object_type, "sales_stage", "Sales Stage", "string", "text")
    ensure_custom_property(object_type, "engagement_status", "Engagement Status", "string", "text")
    ensure_custom_property(object_type, "email_open_rate", "Email Open Rate", "number", "number")
    # Do not attempt to create lead status since hs_lead_status is built-in.
    try:
        props_response = client.crm.properties.core_api.get_all(object_type=object_type)
        existing = [prop.name for prop in props_response.results] if hasattr(props_response, "results") else []
        if "hs_lead_status" in existing:
            print("Using built-in hs_lead_status for lead status.")
        else:
            print("hs_lead_status property not found; please ensure your account supports it.")
    except Exception as e:
        print(f"Error checking for hs_lead_status: {e}")

def get_valid_lead_status_options():
    """
    Retrieves valid options for the built-in hs_lead_status property.
    Returns a list of allowed values.
    """
    try:
        props_response = client.crm.properties.core_api.get_all(object_type="contacts")
        for prop in props_response.results:
            if prop.name == "hs_lead_status" and hasattr(prop, "options") and prop.options:
                # Return the allowed values (the 'value' field of each option)
                return [option.value for option in prop.options]
    except Exception as e:
        print(f"Error retrieving hs_lead_status options: {e}")
    return []

def create_synthetic_contacts(count=100):
    """
    Creates synthetic contacts with additional fields for sales, engagement, and lead status.
    Uses the valid options for hs_lead_status retrieved from the API.
    """
    print("Creating synthetic contacts...")

    # Sample values for sales and engagement.
    sales_stages = ["Prospect", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    engagement_statuses = ["Not Engaged", "Engaged", "Highly Engaged"]

    # Retrieve valid lead status options from the API.
    valid_lead_statuses = get_valid_lead_status_options()
    if not valid_lead_statuses:
        print("Could not retrieve valid lead status options. Defaulting to 'NEW'.")
        valid_lead_statuses = ["NEW"]

    contacts = []
    for _ in range(count):
        properties = {
            "firstname": fake.first_name(),
            "lastname": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "company": fake.company(),
            # Custom properties for sales and engagement.
            "sales_stage": random.choice(sales_stages),
            "engagement_status": random.choice(engagement_statuses),
            "email_open_rate": round(random.uniform(0, 100), 2),  # percentage value
            # Use a valid hs_lead_status value.
            "hs_lead_status": random.choice(valid_lead_statuses)
        }
        contacts.append(SimplePublicObjectInput(properties=properties))

    batch_input = BatchInputSimplePublicObjectBatchInput(inputs=contacts)
    try:
        response = client.crm.contacts.batch_api.create(
            batch_input_simple_public_object_input_for_create=batch_input
        )
        print("Contacts created successfully.")
        print(response)
    except Exception as e:
        print("An error occurred while creating contacts:")
        print(e)

def main():
    # Delete existing contacts.
    delete_all_contacts()
    sleep(1)
    # Ensure custom properties exist.
    create_custom_properties_for_contacts()
    sleep(1)
    # Create synthetic contacts.
    create_synthetic_contacts(count=100)

if __name__ == "__main__":
    main()
