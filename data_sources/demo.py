"""
Demo data source for ResellSquare
Returns sample data for testing the application
"""

import random


class DemoDataSource:
      """Demo data source that returns sample product data"""

    def __init__(self):
              # Sample product data for demo purposes
              self.demo_products = {
                            'iphone': {
                                              'titles': [
                                                                    'Apple iPhone 14 Pro Max 256GB Space Black',
                                                                    'iPhone 14 Pro 128GB Deep Purple Unlocked',
                                                                    'Apple iPhone 14 Pro Max 512GB Gold',
                                                                    'iPhone 14 Pro 256GB Silver - Excellent Condition',
                                                                    'Apple iPhone 14 Pro Max 1TB Space Black',
                                                                    'iPhone 14 Pro 128GB Space Black Unlocked',
                                                                    'Apple iPhone 14 Pro 256GB Deep Purple',
                                                                    'iPhone 14 Pro Max 256GB Silver Like New',
                                              ],
                                              'prices': [899.99, 849.00, 999.99, 875.00, 1099.00, 825.00, 895.00, 925.00]
                            },
                            'macbook': {
                                              'titles': [
                                                                    'MacBook Pro 14" M3 Pro 18GB 512GB Space Black',
                                                                    'Apple MacBook Air 15" M2 16GB 256GB Midnight',
                                                                    'MacBook Pro 16" M3 Max 36GB 1TB Silver',
                                                                    'MacBook Air 13" M2 8GB 256GB Starlight',
                                                                    'Apple MacBook Pro 14" M3 8GB 512GB Silver',
                                              ],
                                              'prices': [1799.00, 1199.00, 2899.00, 999.00, 1499.00]
                            },
                            'airpods': {
                                              'titles': [
                                                                    'Apple AirPods Pro 2nd Gen with MagSafe Case',
                                                                    'AirPods Max Space Gray - Excellent Condition',
                                                                    'Apple AirPods 3rd Generation with MagSafe',
                                                                    'AirPods Pro 2 USB-C - Like New',
                                                                    'Apple AirPods Max Silver',
                                              ],
                                              'prices': [189.99, 399.00, 149.99, 199.00, 425.00]
                            }
              }

        # Generic fallback data
              self.generic_data = {
                  'titles': [
                      'Sample Product Item 1 - Great Condition',
                      'Sample Product Item 2 - Like New',
                      'Sample Product Item 3 - Excellent',
                      'Sample Product Item 4 - Good Condition',
                      'Sample Product Item 5 - New in Box',
                  ],
                  'prices': [49.99, 59.99, 45.00, 55.00, 65.00]
              }

    def fetch(self, search_term: str) -> dict:
              """
                      Fetch demo data for a search term.
                              Returns data in the format expected by app.py
                                      """
              search_lower = search_term.lower()

        # Check if we have specific demo data for this search term
              for keyword, data in self.demo_products.items():
                            if keyword in search_lower:
                                              return {
                                                                    'status': 'ok',
                                                                    'search_term': search_term,
                                                                    'titles': data['titles'],
                                                                    'prices': data['prices']
                                              }

                        # Return generic data with some randomization for other searches
                        prices = [round(random.uniform(20, 200), 2) for _ in range(5)]
        titles = [f"{search_term} - Item {i+1}" for i in range(5)]

        return {
                      'status': 'ok',
                      'search_term': search_term,
                      'titles': titles,
                      'prices': prices
        }
