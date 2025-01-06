from django.test import TestCase
from rest_framework.test import APITestCase 
from django.contrib.auth.models import User
from coder_app.models import Order, Offer, OfferDetail, BusinessProfile, CustomerProfile, Review, User
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from coder_app.serializers import (LoginSerializer,OrderSerializer,
                             OfferSerializer,BusinessProfileSerializer, 
                             CustomerProfileSerializer, User,OfferDetailSerializer,RegistrationSerializer
                             )
from coder_app.models import Offer, OfferDetail
from decimal import Decimal


from django.contrib.admin.sites import site
from coder_app.admin import CustomerProfileAdmin
from coder_app.admin import BusinessProfileAdmin
from coder_app.admin import OfferAdmin
from coder_app.admin import OrderAdmin
from coder_app.admin import ReviewAdmin
from coder_app.admin import OfferDetailAdmin

from django.core.exceptions import ValidationError

# admin_logic.py

class OfferDetailAdminTest(TestCase):

    def setUp(self):
        # Erstelle Benutzer für die Tests
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.client.login(username='admin', password='adminpass')

        # Erstelle ein Angebot
        self.offer = Offer.objects.create(title='Test Offer', description='This is a test offer.', price=99.99)

        # Erstelle ein Angebot Detail
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            variant_title='Test Variant',
            variant_price=49.99,
            delivery_time_in_days=5,
            offer_type='Standard'  # Beispieltyp
        )

    def test_offer_detail_admin_registered(self):
        # Teste, ob das OfferDetailAdmin im Admin-Bereich registriert ist
        self.assertIn(OfferDetail, site._registry)
        self.assertIsInstance(site._registry[OfferDetail], OfferDetailAdmin)

    def test_offer_detail_change_view(self):
        # Teste die Änderungsansicht für das Angebot Detail
        response = self.client.get(reverse('admin:coder_app_offerdetail_change', args=[self.offer_detail.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Variant')  # Überprüfe, ob der Variant Titel im Formular angezeigt wird

    def test_offer_detail_add_view(self):
        # Teste die Hinzufügungsansicht für das Angebot Detail
        response = self.client.get(reverse('admin:coder_app_offerdetail_add'))
        self.assertEqual(response.status_code, 200)

    def test_offer_detail_list_view(self):
        # Teste die Listenansicht für das Angebot Detail
        response = self.client.get(reverse('admin:coder_app_offerdetail_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Variant')  # Überprüfe, ob der Variant Titel in der Liste angezeigt wird

    def test_offer_detail_search(self):
        # Teste die Suchfunktion für das Angebot Detail
        response = self.client.get(reverse('admin:coder_app_offerdetail_changelist') + '?q=Test Variant')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Variant')  # Überprüfe, ob der Variant Titel in den Suchergebnissen angezeigt wird

    def test_offer_detail_filter(self):
        # Teste die Filterfunktion für das Angebot Detail
        response = self.client.get(reverse('admin:coder_app_offerdetail_changelist') + '?offer_type=Standard')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Variant')  # Überprüfe, ob der Variant Titel in den gefilterten Ergebnissen angezeigt wird

class ReviewAdminTest(TestCase):

    def setUp(self):
    # Erstelle Benutzer für die Tests
    
        self.reviewer = User.objects.create_user(username='reviewer', password='reviewerpass', email='reviewer@example.com')
        self.business_user = User.objects.create_user(username='business', password='businesspass', email='business@example.com')
        self.offer = Offer.objects.create(title='Test Offer', description='This is a test offer.', price=99.99)  # Beispielangebot
        self.review = Review.objects.create(
            reviewer=self.reviewer,
            business_user=self.business_user,
            rating=5,
            description='Great service!',  # Verwende das richtige Feld
            offer=self.offer,
        )
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.client.login(username='admin', password='adminpass')
        print(Review.objects.all()) 

    def test_review_admin_registered(self):
        # Teste, ob das ReviewAdmin im Admin-Bereich registriert ist
        self.assertIn(Review, site._registry)
        self.assertIsInstance(site._registry[Review], ReviewAdmin)

    def test_review_change_view(self):
        # Teste die Änderungsansicht für die Bewertung
        response = self.client.get(reverse('admin:coder_app_review_change', args=[self.review.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Great service!')  # Überprüfe, ob die Beschreibung im Formular angezeigt wird

    def test_review_add_view(self):
        # Teste die Hinzufügungsansicht für die Bewertung
        response = self.client.get(reverse('admin:coder_app_review_add'))
        self.assertEqual(response.status_code, 200)

    def test_review_list_view(self):
        # Teste die Listenansicht für die Bewertung
        response = self.client.get(reverse('admin:coder_app_review_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'reviewer')  # Überprüfe, ob die Beschreibung in der Liste angezeigt wird

    def test_review_filter(self):
    # Teste die Filterfunktion für die Bewertung
        response = self.client.get(reverse('admin:coder_app_review_changelist') + '?rating=5')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'reviewer')  # Überprüfe, ob der Name des Reviewers in den gefilterten Ergebnissen angezeigt wird

    def test_review_search(self):
    # Teste die Suchfunktion für die Bewertung
        response = self.client.get(reverse('admin:coder_app_review_changelist') + '?q=reviewer')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'reviewer')  # Überprüfe, ob der Name des Reviewers in den Suchergebnissen angezeigt wird

class OrderAdminTest(TestCase):

    def setUp(self):
        # Erstelle Benutzer für die Tests
        self.user = User.objects.create_user(username='customer', password='customerpass', email='customer@example.com')
        self.business_user = User.objects.create_user(username='business', password='businesspass', email='business@example.com')
        self.offer = Offer.objects.create(title='Test Offer', description='This is a test offer.', price=99.99)
        self.order = Order.objects.create(
            user=self.user,
            business_user=self.business_user,
            offer=self.offer,
            status='Pending',  # Beispielstatus
            option='Standard',  # Beispieloption
        )
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.client.login(username='admin', password='adminpass')

    def test_order_admin_registered(self):
        # Teste, ob das OrderAdmin im Admin-Bereich registriert ist
        self.assertIn(Order, site._registry)
        self.assertIsInstance(site._registry[Order], OrderAdmin)

    def test_order_change_view(self):
        # Teste die Änderungsansicht für die Bestellung
        response = self.client.get(reverse('admin:coder_app_order_change', args=[self.order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob das Angebot im Formular angezeigt wird

    def test_order_add_view(self):
        # Teste die Hinzufügungsansicht für die Bestellung
        response = self.client.get(reverse('admin:coder_app_order_add'))
        self.assertEqual(response.status_code, 200)

    def test_order_list_view(self):
        # Teste die Listenansicht für die Bestellung
        response = self.client.get(reverse('admin:coder_app_order_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob das Angebot in der Liste angezeigt wird

    def test_order_search(self):
        # Teste die Suchfunktion für die Bestellung
        response = self.client.get(reverse('admin:coder_app_order_changelist') + '?q=customer')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob die Bestellung in den Suchergebnissen angezeigt wird

    def test_order_filter(self):
        # Teste die Filterfunktion für die Bestellung
        response = self.client.get(reverse('admin:coder_app_order_changelist') + '?status=Pending')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob die Bestellung in den gefilterten Ergebnissen angezeigt wird

class OfferAdminTest(TestCase):

    def setUp(self):
        # Erstelle einen Superuser für die Tests
        self.user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.client.login(username='admin', password='adminpass')
        self.offer = Offer.objects.create(
            title='Test Offer',
            description='This is a test offer.',
            price=99.99,
            delivery_time_in_days=5,
        )

    def test_offer_admin_registered(self):
        # Teste, ob das OfferAdmin im Admin-Bereich registriert ist
        self.assertIn(Offer, site._registry)
        self.assertIsInstance(site._registry[Offer], OfferAdmin)

    def test_offer_change_view(self):
        # Teste die Änderungsansicht für das Angebot
        response = self.client.get(reverse('admin:coder_app_offer_change', args=[self.offer.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob der Titel im Formular angezeigt wird

    def test_offer_add_view(self):
        # Teste die Hinzufügungsansicht für das Angebot
        response = self.client.get(reverse('admin:coder_app_offer_add'))
        self.assertEqual(response.status_code, 200)

    def test_offer_list_view(self):
        # Teste die Listenansicht für das Angebot
        response = self.client.get(reverse('admin:coder_app_offer_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob der Titel in der Liste angezeigt wird

    def test_offer_search(self):
        # Teste die Suchfunktion für das Angebot
        response = self.client.get(reverse('admin:coder_app_offer_changelist') + '?q=Test Offer')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob das Angebot in den Suchergebnissen angezeigt wird

    def test_offer_filter(self):
        # Teste die Filterfunktion für das Angebot
        response = self.client.get(reverse('admin:coder_app_offer_changelist') + '?price__exact=99.99')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Offer')  # Überprüfe, ob das Angebot in den gefilterten Ergebnissen angezeigt wird

class BusinessProfileAdminTest(TestCase):

    def setUp(self):
        # Erstelle einen Superuser für die Tests
        self.user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.client.login(username='admin', password='adminpass')
        self.business_profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='123 Test St, Test City',
            description='This is a test company.',
            tel='1234567890',
            location='Test Location',
            working_hours='9 AM - 5 PM',
            email='info@testcompany.com'  # Diese E-Mail gehört zum BusinessProfile
        )

    def test_business_profile_admin_registered(self):
        # Teste, ob das BusinessProfileAdmin im Admin-Bereich registriert ist
        self.assertIn(BusinessProfile, site._registry)
        self.assertIsInstance(site._registry[BusinessProfile], BusinessProfileAdmin)

    def test_business_profile_change_view(self):
        # Teste die Änderungsansicht für das Business-Profil
        response = self.client.get(reverse('admin:coder_app_businessprofile_change', args=[self.business_profile.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Company')  # Überprüfe, ob der Firmenname im Formular angezeigt wird

    def test_business_profile_add_view(self):
        # Teste die Hinzufügungsansicht für das Business-Profil
        response = self.client.get(reverse('admin:coder_app_businessprofile_add'))
        self.assertEqual(response.status_code, 200)

    def test_business_profile_list_view(self):
        # Teste die Listenansicht für das Business-Profil
        response = self.client.get(reverse('admin:coder_app_businessprofile_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Company')  # Überprüfe, ob der Firmenname in der Liste angezeigt wird

    def test_profile_image_preview(self):
        # Teste die Vorschau des Profilbilds
        self.business_profile.profile_image = 'path/to/image.jpg'  # Setze einen Beispielpfad
        self.business_profile.save()
        response = self.client.get(reverse('admin:coder_app_businessprofile_change', args=[self.business_profile.id]))
        self.assertContains(response, 'path/to/image.jpg')  # Überprüfe, ob der Bildpfad in der Antwort enthalten ist

    def test_get_username(self):
        # Teste die Funktion get_username
        response = self.client.get(reverse('admin:coder_app_businessprofile_change', args=[self.business_profile.id]))
        self.assertContains(response, 'admin')  # Überprüfe, ob der Benutzername angezeigt wird

class CustomerProfileAdminTest(TestCase):

    def setUp(self):
        # Erstelle einen Superuser für die Tests
        self.user = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com')
        self.client.login(username='admin', password='adminpass')
        self.customer_profile = CustomerProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe'
        )

    def test_customer_profile_admin_registered(self):
        # Teste, ob das CustomerProfileAdmin im Admin-Bereich registriert ist
        self.assertIn(CustomerProfile, site._registry)
        self.assertIsInstance(site._registry[CustomerProfile], CustomerProfileAdmin)

    def test_customer_profile_change_view(self):
        # Teste die Änderungsansicht für das Kundenprofil
        response = self.client.get(reverse('admin:coder_app_customerprofile_change', args=[self.customer_profile.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')  # Überprüfe, ob der Name im Formular angezeigt wird

    def test_customer_profile_add_view(self):
        # Teste die Hinzufügungsansicht für das Kundenprofil
        response = self.client.get(reverse('admin:coder_app_customerprofile_add'))
        self.assertEqual(response.status_code, 200)

    def test_customer_profile_list_view(self):
        # Teste die Listenansicht für das Kundenprofil
        response = self.client.get(reverse('admin:coder_app_customerprofile_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')  # Überprüfe, ob der Name in der Liste angezeigt wird

    def test_profile_image_preview(self):
        # Teste die Vorschau des Profilbilds
        self.customer_profile.file = 'path/to/image.jpg'  # Setze einen Beispielpfad
        self.customer_profile.save()
        response = self.client.get(reverse('admin:coder_app_customerprofile_change', args=[self.customer_profile.id]))
        self.assertContains(response, 'path/to/image.jpg')  # Überprüfe, ob der Bildpfad in der Antwort enthalten ist

# End of admin_logic.py


# model_logic.py
class OrderModelTest(TestCase):

    def setUp(self):
        # Erstelle Benutzer für die Tests
        self.business_user = User.objects.create_user(username='businessuser', password='businesspass')
        self.customer_user = User.objects.create_user(username='customeruser', password='customerpass')
        self.offer = Offer.objects.create(
            title='Test Offer',
            description='This is a test offer.',
            price=99.99,
            delivery_time_in_days=5,
            user=self.business_user
        )
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            features=['Feature 1', 'Feature 2']
        )

    def test_order_creation(self):
        # Teste die Erstellung einer Bestellung
        order = Order.objects.create(
            user=self.customer_user,
            offer=self.offer,
            offer_detail_id=self.offer_detail
        )
        self.assertEqual(order.user, self.customer_user)
        self.assertEqual(order.offer, self.offer)
        self.assertEqual(order.offer_detail_id, self.offer_detail)
        self.assertEqual(order.status, 'pending')  # Standardstatus sollte 'pending' sein
        self.assertEqual(order.business_user, self.business_user)  # business_user sollte gesetzt werden

    def test_set_features_from_offer_detail_if_missing(self):
        # Teste, ob die Features von OfferDetail gesetzt werden
        order = Order.objects.create(
            user=self.customer_user,
            offer=self.offer,
            offer_detail_id=self.offer_detail
        )
        self.assertEqual(order.features, ['Feature 1', 'Feature 2'])  # Features sollten gesetzt werden

    def test_set_business_user_if_missing(self):
        # Teste, ob der business_user gesetzt wird, wenn er nicht angegeben ist
        order = Order.objects.create(
            user=self.customer_user,
            offer=self.offer,
            offer_detail_id=self.offer_detail,
            business_user=None  # business_user nicht setzen
        )
        self.assertEqual(order.business_user, self.business_user)  # business_user sollte gesetzt werden

    def test_order_status_choices(self):
        # Teste die Statuswahl
        order = Order.objects.create(
            user=self.customer_user,
            offer=self.offer,
            offer_detail_id=self.offer_detail
        )
        self.assertIn(order.status, dict(Order.STATUS_CHOICES))  # Status sollte in den Wahlmöglichkeiten sein

class CustomerProfileModelTest(TestCase):

    def setUp(self):
        # Erstelle einen Benutzer für die Tests
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_customer_profile_creation(self):
        # Teste die Erstellung eines Kundenprofils
        profile = CustomerProfile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(profile.first_name, 'John')
        self.assertEqual(profile.last_name, 'Doe')
        self.assertEqual(profile.user, self.user)

    def test_string_representation(self):
        # Teste die String-Repräsentation des Kundenprofils
        profile = CustomerProfile(user=self.user, first_name='John', last_name='Doe')
        self.assertEqual(str(profile), 'John Doe')

class BusinessProfileModelTest(TestCase):

    def setUp(self):
        # Erstelle einen Benutzer für die Tests
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_business_profile_creation(self):
        # Teste die Erstellung eines Business-Profils
        profile = BusinessProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='123 Test St, Test City',
            description='This is a test company.',
            tel='1234567890',
            location='Test Location',
            working_hours='9 AM - 5 PM',
            email='info@testcompany.com'
        )
        self.assertEqual(profile.company_name, 'Test Company')
        self.assertEqual(profile.company_address, '123 Test St, Test City')
        self.assertEqual(profile.description, 'This is a test company.')
        self.assertEqual(profile.tel, '1234567890')
        self.assertEqual(profile.location, 'Test Location')
        self.assertEqual(profile.working_hours, '9 AM - 5 PM')
        self.assertEqual(profile.email, 'info@testcompany.com')
        self.assertEqual(profile.user, self.user)

    def test_string_representation(self):
        # Teste die String-Repräsentation des Business-Profils
        profile = BusinessProfile(user=self.user, company_name='Test Company')
        self.assertEqual(str(profile), 'Test Company')

class ReviewModelTest(TestCase):

    def setUp(self):
        # Erstelle Benutzer für die Tests
        self.business_user = User.objects.create_user(username='businessuser', password='businesspass')
        self.reviewer = User.objects.create_user(username='reviewer', password='reviewpass')
        self.offer = Offer.objects.create(
            title='Test Offer',
            description='This is a test offer.',
            price=99.99,
            delivery_time_in_days=5,
            user=self.business_user
        )

    def test_review_creation(self):
        # Teste die Erstellung einer Bewertung
        review = Review.objects.create(
            rating=5,
            description='Great offer!',
            business_user=self.business_user,
            reviewer=self.reviewer,
            offer=self.offer
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.description, 'Great offer!')
        self.assertEqual(review.business_user, self.business_user)
        self.assertEqual(review.reviewer, self.reviewer)
        self.assertEqual(review.offer, self.offer)

    def test_string_representation(self):
        # Teste die String-Repräsentation der Bewertung
        review = Review(
            rating=5,
            description='Great offer!',
            business_user=self.business_user,
            reviewer=self.reviewer,
            offer=self.offer
        )
        self.assertEqual(str(review), f'Review by {self.reviewer} for (Business: {self.business_user}, Offer: {self.offer})')

    def test_review_ordering(self):
    # Teste die Sortierung der Bewertungen
        review1 = Review.objects.create(
            rating=4,
            description='Good offer!',
            business_user=self.business_user,
            reviewer=self.reviewer,
            offer=self.offer
        )
    
    # Füge eine kurze Verzögerung hinzu, um sicherzustellen, dass die Zeitstempel unterschiedlich sind
        import time
        time.sleep(1)  # Warte 1 Sekunde

        review2 = Review.objects.create(
            rating=5,
            description='Excellent offer!',
            business_user=self.business_user,
            reviewer=self.reviewer,
            offer=self.offer
        )
    
        reviews = Review.objects.all()
        self.assertEqual(list(reviews), [review2, review1])  # review2 sollte zuerst kommen

class OfferModelTest(TestCase):

    def setUp(self):
        # Erstelle einen Benutzer für die Tests
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_offer_creation(self):
        # Teste die Erstellung eines Angebots
        offer = Offer.objects.create(
            title='Test Offer',
            description='This is a test offer.',
            price=99.99,
            delivery_time_in_days=5,
            user=self.user
        )
        self.assertEqual(offer.title, 'Test Offer')
        self.assertEqual(offer.description, 'This is a test offer.')
        self.assertEqual(offer.price, 99.99)
        self.assertEqual(offer.delivery_time_in_days, 5)
        self.assertEqual(offer.user, self.user)

    def test_min_price(self):
        # Teste die min_price Methode
        offer = Offer.objects.create(
            title='Test Offer',
            description='This is a test offer.',
            price=49.99,
            user=self.user
        )
        self.assertEqual(offer.min_price(), 49.99)

    def test_min_delivery_time(self):
        # Teste die min_delivery_time Methode
        offer = Offer.objects.create(
            title='Test Offer',
            description='This is a test offer.',
            delivery_time_in_days=3,
            user=self.user
        )
        self.assertEqual(offer.min_delivery_time(), 3)

    def test_string_representation(self):
        # Teste die String-Repräsentation des Angebots
        offer = Offer(title='Test Offer')
        self.assertEqual(str(offer), 'Test Offer')
        



class OfferDetailModelTest(TestCase):

    def setUp(self):
        # Erstelle ein Angebot, um es mit OfferDetail zu verknüpfen
        self.offer = Offer.objects.create(title="Test Offer", description="Test Description", price=100.00)

    def test_create_offer_detail(self):
        # Teste die Erstellung einer OfferDetail-Instanz
        offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            variant_title="Test Variant",
            variant_price=29.99,
            delivery_time_in_days=5,
            revision_limit=3,
            additional_details="Some additional details",
            offer_type="basic",
            features=["Feature 1", "Feature 2"]
        )
        self.assertIsInstance(offer_detail, OfferDetail)
        self.assertEqual(offer_detail.variant_title, "Test Variant")
        self.assertEqual(offer_detail.variant_price, 29.99)
        self.assertEqual(offer_detail.delivery_time_in_days, 5)
        self.assertEqual(offer_detail.revision_limit, 3)
        self.assertEqual(offer_detail.additional_details, "Some additional details")
        self.assertEqual(offer_detail.offer_type, "basic")
        self.assertEqual(offer_detail.features, ["Feature 1", "Feature 2"])

    def test_str_method(self):
        # Teste die __str__-Methode
        offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            variant_title="Test Variant",
            variant_price=29.99,
            delivery_time_in_days=5,
            revision_limit=3,
            additional_details="Some additional details",
            offer_type="premium"
        )
        self.assertEqual(str(offer_detail), "premium - Test Variant")

    def test_variant_price_validation(self):
        # Teste die Validierung für variant_price mit einem ungültigen Wert
        offer_detail = OfferDetail(
            offer=self.offer,
            variant_title="Test Variant",
            variant_price="invalid",  # Ungültiger Wert
            delivery_time_in_days=5,
            revision_limit=3,
            additional_details="Some additional details",
            offer_type="basic",
            features=["Feature 1", "Feature 2"]  # Setze gültige Features
        )
        with self.assertRaises(ValidationError):
            offer_detail.full_clean()  # Dies sollte eine Validierungsfehler auslösen

    def test_offer_type_choices(self):
        # Teste die Auswahlmöglichkeiten für offer_type
        offer_detail = OfferDetail(offer=self.offer, variant_title="Test Variant", offer_type="standard")
        self.assertIn(offer_detail.offer_type, dict(OfferDetail._meta.get_field('offer_type').choices))

#End of model_logic.py



# serializers_logic.py
class ReviewSerializerTests(APITestCase):

    def setUp(self):
        """
        Set up test users, profiles, and reviews.
        """
        self.business_user = User.objects.create_user

class CustomerProfileSerializerTests(APITestCase):

    def setUp(self):
        """
        Set up a user and a customer profile for testing.
        """
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.customer_profile = CustomerProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            created_at='2024-01-01'
        )

    def test_serializer_with_valid_data(self):
        """
        Test that the serializer is valid with proper data.
        """
        data = {
            "user": self.user.id,
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = CustomerProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_with_missing_fields(self):
        """
        Test that the serializer raises errors for missing fields.
        """
        data = {
            "user": self.user.id,
        }
        serializer = CustomerProfileSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("first_name", serializer.errors)
        self.assertIn("last_name", serializer.errors)

    def test_serializer_update(self):
        """
        Test that the serializer can update a customer profile.
        """
        data = {
            "first_name": "Updated",
            "last_name": "Name",
        }
        serializer = CustomerProfileSerializer(instance=self.customer_profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_profile = serializer.save()

        self.assertEqual(updated_profile.first_name, "Updated")
        self.assertEqual(updated_profile.last_name, "Name")

    def test_serializer_read_only_user_field(self):
        """
        Test that the `user` field is read-only.
        """
        data = {
            "user": 9999,  # Attempt to change the user
            "first_name": "Invalid Update",
            "last_name": "User"
        }
        serializer = CustomerProfileSerializer(instance=self.customer_profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_profile = serializer.save()

        # Ensure the `user` field has not been updated
        self.assertEqual(updated_profile.user.id, self.user.id)


class OrderSerializerTests(APITestCase):
    def setUp(self):
        # Setup test data
        self.user = User.objects.create(username="test_user")
        self.business_user = User.objects.create(username="business_user")

        self.offer = Offer.objects.create(
            title="Test Offer",
            description="A sample offer",
            price=100.00,
            delivery_time_in_days=5,
            user=self.business_user
        )

        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            variant_title="Basic",
            variant_price=100.00,
            delivery_time_in_days=5,
            revision_limit=2,
            offer_type="basic",
            features=["Feature1", "Feature2"]
        )

        self.order = Order.objects.create(
            user=self.user,
            business_user=self.business_user,
            offer=self.offer,
            offer_detail_id=self.offer_detail,
            status="pending",
            option="basic"
        )

    def test_serializer_with_valid_data(self):
        # Test the serializer with valid data
        serializer = OrderSerializer(instance=self.order)
        data = serializer.data

        self.assertEqual(data["id"], self.order.id)
        self.assertEqual(data["offer_title"], self.offer.title)
        self.assertEqual(data["offer_provider"], self.business_user.username)
        self.assertEqual(data["offer_price"], "100.00")
        self.assertEqual(data["offer_delivery_time"], 5)
        self.assertEqual(data["status_display"], "Pending")
        self.assertEqual(data["features"], ["Feature1", "Feature2"])

    def test_serializer_create(self):
        # Test creating an order with the serializer
        data = {
            "user": self.user.id,
            "offer": self.offer.id,
            "offer_detail_id": self.offer_detail.id,
            "status": "pending",
            "option": "basic"
        }

        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        order = serializer.save()

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.offer, self.offer)
        self.assertEqual(order.offer_detail_id, self.offer_detail)
        self.assertEqual(order.status, "pending")

    def test_serializer_update(self):
        # Test updating an order with the serializer
        data = {
            "status": "in_progress",
            "offer_detail_id": self.offer_detail.id
        }

        serializer = OrderSerializer(instance=self.order, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_order = serializer.save()

        self.assertEqual(updated_order.status, "in_progress")
        self.assertEqual(updated_order.offer_detail_id, self.offer_detail)



class OfferSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user", email="test_user@example.com")
        self.offer_data = {
            "title": "Test Offer",
            "description": "This is a test offer.",
            "price": 100.00,
            "delivery_time_in_days": 7,
            "details": [
                {
                    "title": "Basic Detail",
                    "price": 50.00,
                    "revisions": 2,
                    "delivery_time_in_days": 3,
                    "offer_type": "basic",
                    "features": ["Feature 1", "Feature 2"]
                },
                {
                    "title": "Premium Detail",
                    "price": 150.00,
                    "revisions": 5,
                    "delivery_time_in_days": 1,
                    "offer_type": "premium",
                    "features": ["Feature A", "Feature B"]
                }
            ]
        }
        self.existing_offer = Offer.objects.create(
            user=self.user,
            title="Old Offer",
            description="Old Description",
            price=50.00,
            delivery_time_in_days=5,
        )
        self.old_detail = OfferDetail.objects.create(
            offer=self.existing_offer,
            variant_title="Old Detail",
            variant_price=50.00,
            delivery_time_in_days=3,
            revision_limit=2,
            offer_type="basic",
            features=["Old Feature"]
        )


    def test_serializer_update(self):
        updated_data = {
            "title": "Updated Offer",
            "description": "Updated Description",
            "price": 200.00,
            "delivery_time_in_days": 10,
            "details": [
                {
                    "offer_type": "basic",
                    "title": "Updated Detail",
                    "price": 60.00,
                    "revisions": 3,
                    "delivery_time_in_days": 2,
                    "features": ["Updated Feature 1", "Updated Feature 2"]
               }
            ]
        }

        serializer = OfferSerializer(instance=self.existing_offer, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_offer = serializer.save()
        updated_detail = updated_offer.details.first()

        self.assertEqual(updated_offer.title, "Updated Offer")
        self.assertEqual(updated_offer.price, 200.00)
        self.assertEqual(updated_detail.variant_title, "Updated Detail")
        self.assertEqual(updated_detail.features, ["Updated Feature 1", "Updated Feature 2"])


class BusinessProfileSerializerTests(TestCase):
    def setUp(self):
        # Erstelle einen Benutzer
        self.user = User.objects.create_user(username="testuser", password="testpassword")

        # Erstelle ein gültiges Angebot (Offer)
        self.offer = Offer.objects.create(
            title="Test Offer",
            description="Test Description",
            price=100.00,
            delivery_time_in_days=5,
            user=self.user
        )

        # Erstelle eine Bestellung (Order) mit dem Angebot
        Order.objects.create(
            user=self.user,
            business_user=self.user,
            offer=self.offer,  # Nutze das erstellte Angebot
            status="in_progress"
        )

        # Erstelle ein BusinessProfile
        self.business_profile = BusinessProfile.objects.create(
            user=self.user,
            company_name="Test Company",
            company_address="Test Address",
            tel="1234567890"
        )

    def test_calculate_avg_rating(self):
        serializer = BusinessProfileSerializer(instance=self.business_profile)
        self.assertEqual(serializer.data["avg_rating"], "-")

    def test_count_pending_orders(self):
        serializer = BusinessProfileSerializer(instance=self.business_profile)
        self.assertEqual(serializer.data["pending_orders"], 1)


class OfferDetailSerializerTests(TestCase):
    def setUp(self):
        self.offer = Offer.objects.create(
            title="Test Offer", 
            description="A test offer", 
            price=50.00, 
            delivery_time_in_days=5
        )
        self.offer_detail = OfferDetail.objects.create(
            offer=self.offer,
            variant_title="Standard",
            variant_price=50.00,
            delivery_time_in_days=7,
            revision_limit=3,
            additional_details="Some details",
            offer_type="standard",
            features=["Feature 1", "Feature 2"]
        )

    def test_serializer_with_valid_data(self):
        data = {
            "title": "Updated Title",
            "price": 100.00,
            "revisions": 5,
            "delivery_time_in_days": 10,
            "features": ["Feature 1", "Feature 2"],
            "offer_type": "basic"
        }
        serializer = OfferDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save(offer=self.offer)
        self.assertEqual(instance.variant_title, "Updated Title")

    def test_serializer_with_invalid_data(self):
        invalid_data = {
            "title": "",  # Leerer Titel
            "price": "invalid",  # Ungültiger Preis
            "delivery_time_in_days": 0,  # Ungültige Lieferzeit (kleiner als 1)
            "features": "not a list",  # Ungültige Merkmale (kein Listentyp)
            "offer_type": "invalid_type"  # Ungültiger Angebotstyp
        }
        serializer = OfferDetailSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertIn("price", serializer.errors)
        self.assertIn("delivery_time_in_days", serializer.errors)  # Validierungsfehler
        self.assertIn("features", serializer.errors)


    def test_partial_update(self):
        partial_data = {"price": 60.00}
        serializer = OfferDetailSerializer(instance=self.offer_detail, data=partial_data, partial=True)
        if serializer.is_valid():
            updated_offer_detail = serializer.save()
        self.assertEqual(updated_offer_detail.variant_price, Decimal("60.00"))


class LoginSerializerTests(TestCase):

    def test_valid_login_data(self):
        """
        Test that valid login data is successfully validated.
        """
        data = {
            'username': 'testuser',
            'password': 'securepassword'
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['username'], data['username'])
        self.assertEqual(serializer.validated_data['password'], data['password'])

    def test_missing_username(self):
        """
        Test that missing username returns an error.
        """
        data = {
            'password': 'securepassword'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_missing_password(self):
        """
        Test that missing password returns an error.
        """
        data = {
            'username': 'testuser'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_empty_username(self):
        """
        Test that empty username returns an error.
        """
        data = {
            'username': '',
            'password': 'securepassword'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_empty_password(self):
        """
        Test that empty password returns an error.
        """
        data = {
            'username': 'testuser',
            'password': ''
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)














class RegistrationSerializerTests(TestCase):
    def test_valid_customer_registration(self):
        """
        Test that a valid customer registration is processed successfully with 'type' field.
        """
        data = {
            "username": "testuser",
            "email": "testcustomer@example.com",
            "password": "securepassword",
            "repeated_password": "securepassword",
            "type": "customer"  # Frontend sendet 'type'
        }
        serializer = RegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # Überprüfen, dass Benutzer und Profil erstellt wurden
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertTrue(CustomerProfile.objects.filter(user=user).exists())

    def test_valid_business_registration(self):
        """
        Test that a valid business registration is processed successfully with 'type' field.
        """
        data = {
            "username": "bizuser",
            "email": "testbusiness@example.com",
            "password": "securepassword",
            "repeated_password": "securepassword",
            "type": "business"  # Frontend sendet 'type'
        }
        serializer = RegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # Überprüfen, dass Benutzer und Profil erstellt wurden
        self.assertTrue(User.objects.filter(username="bizuser").exists())
        self.assertTrue(BusinessProfile.objects.filter(user=user).exists())

    def test_invalid_profile_type(self):
        """
        Test that an invalid profile type raises a validation error.
        """
        data = {
            "username": "invaliduser",
            "email": "invalidprofile@example.com",
            "password": "securepassword",
            "repeated_password": "securepassword",
            "type": "invalid"  # Ungültiger Profiltyp
        }
        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("profile_type", serializer.errors)

    def test_password_mismatch(self):
        """
        Test that mismatched passwords raise a validation error.
        """
        data = {
            "username": "mismatchuser",
            "email": "mismatch@example.com",
            "password": "password123",
            "repeated_password": "password456",
            "type": "customer"  # Frontend sendet 'type'
        }
        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_duplicate_email(self):
        """
        Test that a duplicate email raises a validation error.
        """
        User.objects.create(username="existinguser", email="duplicate@example.com", password="dummy")
        data = {
            "username": "newuser",
            "email": "duplicate@example.com",
            "password": "securepassword",
            "repeated_password": "securepassword",
            "type": "business"  # Frontend sendet 'type'
        }
        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_missing_type_field(self):
        """
        Test that missing 'type' field raises a validation error.
        """
        data = {
            "username": "missingtype",
            "email": "missingtype@example.com",
            "password": "securepassword",
            "repeated_password": "securepassword"
        }
        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("profile_type", serializer.errors)

    def test_missing_email(self):
        """
        Test that missing email raises a validation error.
        """
        data = {
            "username": "noemailuser",
            "password": "securepassword",
            "repeated_password": "securepassword",
            "type": "customer"  # Frontend sendet 'type'
        }
        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

