from valthera.connectors.base import BaseConnector


class MockHubSpotConnector(BaseConnector):
    """
    High lead score and strong marketing engagement -> saturates those factors for motivation.
    """
    def get_user_data(self, user_id: str):
        return {
            "hubspot_contact_id": "999-ZZZ",
            "lifecycle_stage": "opportunity",
            "lead_status": "engaged",
            "lead_score": 100,  # 100 -> lead_score_factor = 1.0
            "company_name": "MaxMotivation Corp.",
            "last_contacted_date": "2023-09-20",
            "marketing_emails_opened": 20,
            "marketing_emails_clicked": 10            
        }
