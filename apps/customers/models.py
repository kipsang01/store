from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"


    @receiver(post_save, sender=User)
    def create_customer_profile(sender, instance, created, **kwargs):
        """
        Create customer profile when user is created
        """
        if created:
            Customer.objects.create(user=instance)


    @receiver(post_save, sender=User)
    def save_customer_profile(sender, instance, **kwargs):
        """
        Save customer profile when user is saved
        """
        try:
            instance.customer.save()
        except Customer.DoesNotExist:
            Customer.objects.create(user=instance)


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'is_verified': self.is_verified,
        }