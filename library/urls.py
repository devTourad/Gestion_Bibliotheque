from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('gallery/', views.book_gallery, name='book_gallery'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Emprunts et réservations
    path('books/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('books/<int:book_id>/reserve/', views.reserve_book, name='reserve_book'),
    path('books/<int:book_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('favorites/<int:favorite_id>/note/', views.add_favorite_note, name='add_favorite_note'),

    # AJAX endpoints
    path('books/<int:book_id>/queue-info/', views.get_book_queue_info, name='get_book_queue_info'),

    # Test pages
    path('test-favorites/', views.test_favorites, name='test_favorites'),

    # Gestion des images (staff seulement)
    path('books/<int:book_id>/upload-cover/', views.upload_book_cover, name='upload_book_cover'),
    path('books/<int:book_id>/search-images/', views.search_book_images, name='search_book_images'),
    path('books/<int:book_id>/download-image/', views.download_image_from_url, name='download_image_from_url'),
    path('admin/bulk-upload-covers/', views.bulk_upload_covers, name='bulk_upload_covers'),

    # Achats de livres
    path('books/<int:book_id>/purchase/', views.purchase_book, name='purchase_book'),
    path('purchases/<int:purchase_id>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:purchase_id>/cancel/', views.cancel_purchase, name='cancel_purchase'),
    path('my-purchases/', views.my_purchases, name='my_purchases'),
    path('pay-all-purchases/', views.pay_all_purchases, name='pay_all_purchases'),

    # Paiements et gestion (staff seulement)
    path('payment/<str:payment_type>/<int:object_id>/', views.process_payment, name='process_payment'),
    path('quick-loan/', views.quick_loan, name='quick_loan'),

    # Administration personnalisée
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_users_management, name='admin_users_management'),
    path('admin-books/', views.admin_books_management, name='admin_books_management'),
    path('admin-purchases/', views.admin_purchases, name='admin_purchases'),
    path('admin/purchases/<int:purchase_id>/update-status/', views.admin_update_purchase_status, name='admin_update_purchase_status'),
    path('admin/purchases/<int:purchase_id>/confirm/', views.confirm_purchase, name='confirm_purchase'),
    path('admin/purchases/<int:purchase_id>/mark-paid/', views.mark_purchase_paid, name='mark_purchase_paid'),

    # Gestion des paiements
    path('admin-payments/', views.admin_payments, name='admin_payments'),
    path('admin/payments/<int:payment_id>/update-status/', views.update_payment_status, name='update_payment_status'),

    # Paiements utilisateur
    path('purchase/<int:purchase_id>/pay/', views.initiate_payment, name='initiate_payment'),
    path('payment/<int:payment_id>/process/', views.process_payment, name='process_payment'),
    path('payment/<int:payment_id>/success/', views.payment_success, name='payment_success'),
    path('payment/<int:payment_id>/failed/', views.payment_failed, name='payment_failed'),

    # Gestion des livraisons
    path('admin-purchases/<int:purchase_id>/create-delivery/', views.create_delivery, name='create_delivery'),
    path('admin-deliveries/', views.admin_deliveries, name='admin_deliveries'),
    path('admin-deliveries/<int:delivery_id>/', views.delivery_detail, name='delivery_detail'),
    path('admin-deliveries/<int:delivery_id>/update/', views.update_delivery_status, name='update_delivery_status'),

    # Livraisons utilisateur
    path('launch-all-deliveries/', views.launch_all_deliveries, name='launch_all_deliveries'),
    path('admin/launch-delivery/<int:purchase_id>/', views.admin_launch_delivery, name='admin_launch_delivery'),

    # Super Admin
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/users/', views.manage_admin_users, name='manage_admin_users'),
    path('super-admin/users/<int:user_id>/promote/', views.promote_user, name='promote_user'),
    path('super-admin/settings/', views.system_settings, name='system_settings'),

    # Debug
    path('debug/permissions/', views.debug_permissions, name='debug_permissions'),
    path('debug/urls/', views.test_urls, name='test_urls'),
    path('debug/create-test-purchase/', views.create_test_purchase, name='create_test_purchase'),
    path('debug/outstanding-fees/', views.debug_outstanding_fees, name='debug_outstanding_fees'),
    path('debug/fix-outstanding-fees/', views.fix_outstanding_fees, name='fix_outstanding_fees'),
    path('admin-statistics/', views.admin_statistics, name='admin_statistics'),

    # Emprunts et réservations utilisateur
    path('my-loans/', views.my_loans, name='my_loans'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('my-payments/', views.my_payments, name='my_payments'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),
    path('loans/<int:loan_id>/renew/', views.renew_loan, name='renew_loan'),
    path('pay-all-loans/', views.pay_all_loans, name='pay_all_loans'),

    # Gestion admin des emprunts et réservations
    path('admin-loans/', views.admin_loans, name='admin_loans'),
    path('admin-reservations/', views.admin_reservations, name='admin_reservations'),
    path('loans/<int:loan_id>/return/', views.return_book, name='return_book'),
    path('reservations/<int:reservation_id>/fulfill/', views.fulfill_reservation, name='fulfill_reservation'),

    # Informations
    path('conditions/', views.library_conditions, name='library_conditions'),

    # Authentification
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Actions rapides pour l'administration
    path('admin/library/bookpurchase/<int:purchase_id>/confirm/', views.admin_purchase_confirm, name='admin_purchase_confirm'),
    path('admin/library/bookpurchase/<int:purchase_id>/mark_paid/', views.admin_purchase_mark_paid, name='admin_purchase_mark_paid'),
    path('admin/library/bookpurchase/<int:purchase_id>/mark_delivered/', views.admin_purchase_mark_delivered, name='admin_purchase_mark_delivered'),
    path('admin/library/bookpurchase/<int:purchase_id>/cancel/', views.admin_purchase_cancel, name='admin_purchase_cancel'),
]
