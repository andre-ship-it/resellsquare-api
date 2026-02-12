"""
Demo data source for ResellSquare
Returns realistic sample data for testing the analysis pipeline.
Includes conditions and dates to exercise the full pipeline.
"""

import random
from datetime import datetime, timedelta


class DemoDataSource:
        """Demo data source that returns sample product data with conditions"""

    def __init__(self):
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
                                                                            'iPhone 14 Pro 128GB - FOR PARTS NOT WORKING',
                                                                            'iPhone 14 Pro Max Cracked Screen As-Is',
                                                                            'Apple iPhone 14 Pro 256GB - New Sealed',
                                                                            'iPhone 14 Pro Max 256GB Used Good Condition',
                                                    ],
                                                    'prices': [899.99, 849.00, 999.99, 875.00, 1099.00, 825.00, 895.00, 925.00, 150.00, 200.00, 949.00, 850.00],
                                                    'conditions': ['Used', 'Used', 'New', 'Used', 'New', 'Used', 'Used', 'Used', 'For Parts', 'For Parts', 'New', 'Used'],
                                },
                                'macbook': {
                                                    'titles': [
                                                                            'MacBook Pro 14" M3 Pro 18GB 512GB Space Black',
                                                                            'Apple MacBook Air 15" M2 16GB 256GB Midnight',
                                                                            'MacBook Pro 16" M3 Max 36GB 1TB Silver',
                                                                            'MacBook Air 13" M2 8GB 256GB Starlight',
                                                                            'Apple MacBook Pro 14" M3 8GB 512GB Silver',
                                                                            'MacBook Pro 14" M3 Pro - FOR PARTS cracked screen',
                                                                            'MacBook Air M2 13" Used Excellent',
                                                                            'Apple MacBook Pro 16" M3 Pro 36GB 512GB New Sealed',
                                                                            'Lot of 3 MacBook Pro for parts repair',
                                                                            'MacBook Air 15" M2 8GB 256GB - Refurbished',
                                                    ],
                                                    'prices': [1799.00, 1199.00, 2899.00, 999.00, 1499.00, 450.00, 1050.00, 2199.00, 900.00, 1099.00],
                                                    'conditions': ['New', 'Used', 'New', 'Used', 'New', 'For Parts', 'Used', 'New', 'For Parts', 'Refurbished'],
                                },
                                'airpods': {
                                                    'titles': [
                                                                            'Apple AirPods Pro 2nd Gen with MagSafe Case',
                                                                            'AirPods Max Space Gray - Excellent Condition',
                                                                            'Apple AirPods 3rd Generation with MagSafe',
                                                                            'AirPods Pro 2 USB-C - Like New',
                                                                            'Apple AirPods Max Silver',
                                                                            'AirPods Pro 2 New Sealed Apple',
                                                                            'AirPods Pro 1st Gen Used Good',
                                                                            'Apple AirPods Pro 2 - Not Working For Parts',
                                                                            'AirPods 3rd Gen Open Box Like New',
                                                                            'AirPods Max Pink Excellent Condition',
                                                    ],
                                                    'prices': [189.99, 399.00, 149.99, 199.00, 425.00, 219.00, 89.00, 45.00, 159.00, 389.00],
                                                    'conditions': ['Used', 'Used', 'New', 'Used', 'Used', 'New', 'Used', 'For Parts', 'New', 'Used'],
                                },
                                'ps5': {
                                                    'titles': [
                                                                            'Sony PlayStation 5 Disc Edition Console',
                                                                            'PS5 Digital Edition White - Used',
                                                                            'PlayStation 5 Slim Disc 1TB New Sealed',
                                                                            'PS5 Console Bundle with Extra Controller',
                                                                            'Sony PS5 Disc Edition Used Good Condition',
                                                                            'PlayStation 5 Slim Digital New',
                                                                            'PS5 Console Only No Controller - As Is',
                                                                            'Sony PlayStation 5 1TB Disc Excellent',
                                                    ],
                                                    'prices': [425.00, 350.00, 475.00, 499.00, 389.00, 399.00, 280.00, 410.00],
                                                    'conditions': ['Used', 'Used', 'New', 'New', 'Used', 'New', 'Used', 'Used'],
                                },
                }

        self.generic_data = {
                        'titles': [
                                            'Sample Product Item 1 - Great Condition',
                                            'Sample Product Item 2 - Like New',
                                            'Sample Product Item 3 - Excellent',
                                            'Sample Product Item 4 - Good Condition',
                                            'Sample Product Item 5 - New in Box',
                                            'Sample Product Item 6 - Used',
                                            'Sample Product Item 7 - Refurbished',
                                            'Sample Product Item 8 - New Sealed',
                        ],
                        'prices': [49.99, 59.99, 45.00, 55.00, 65.00, 42.00, 52.00, 68.00],
                        'conditions': ['Used', 'Used', 'Used', 'Used', 'New', 'Used', 'Refurbished', 'New'],
        }

    def _generate_dates(self, count):
                """Generate recent dates for demo data"""
                dates = []
                for i in range(count):
                                days_ago = random.randint(1, 60)
                                d = datetime.now() - timedelta(days=days_ago)
                                dates.append(d.strftime('%Y-%m-%dT%H:%M:%S.000Z'))
                            return dates

    def fetch(self, search_term: str) -> dict:
                """
                        Fetch demo data for a search term.
                                Returns data in the standardized format with conditions and dates.
                                        """
        search_lower = search_term.lower()

        for keyword, data in self.demo_products.items():
                        if keyword in search_lower:
                                            titles = data['titles']
                                            prices = data['prices']
                                            conditions = data.get('conditions', ['Used'] * len(titles))
                                            dates = self._generate_dates(len(titles))
                                            return {
                                                'status': 'ok',
                                                'search_term': search_term,
                                                'titles': titles,
                                                'prices': prices,
                                                'conditions': conditions,
                                                'dates': dates,
                                            }

                    # Generic fallback
                    titles = self.generic_data['titles']
        prices = self.generic_data['prices']
        conditions = self.generic_data['conditions']
        dates = self._generate_dates(len(titles))

        return {
                        'status': 'ok',
                        'search_term': search_term,
                        'titles': [t.replace('Sample Product', search_term) for t in titles],
                        'prices': prices,
                        'conditions': conditions,
                        'dates': dates,
        }
