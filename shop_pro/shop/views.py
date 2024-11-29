from django.shortcuts import render
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import  HttpResponseForbidden, JsonResponse
from .models import Address, Category, Product
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem, Product
from django.views.generic import View
from .models import Cart, Checkout
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator


# To sign in for a user
class RegisterView(FormView):
    template_name = 'shop/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True  # Ensure the account is active
        user.save()
        messages.success(self.request, 'Your account has been created! You are now able to log in.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error creating your account.')
        return super().form_invalid(form)


# Home page weher all the content is 
class HomePageView(View):
    def get(self, request):
        products = Product.objects.all()
        categories = Category.objects.all()
        context = {
            'products': products,
            'categories': categories
        }
        return render(request, 'shop/home.html', context)
    


# Details of the product     
class ProductDetailView(View):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        return render(request, 'shop/product_detail.html', {'product': product})
    


# logout for user account
class LogoutConfirmView(TemplateView):
    template_name = 'shop/logout_confirm.html'


# All the category of products in the site
class CategoryProductsView(ListView):
    model = Product
    template_name = 'shop/category_products.html'
    context_object_name = 'products'

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        category = get_object_or_404(Category, id=category_id)
        return Product.objects.filter(category=category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category, id=self.kwargs['category_id'])
        return context



# To add the new product
class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    success_url = reverse_lazy('product_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to perform this action.")
        return super().dispatch(request, *args, **kwargs)


# To make changes in the product deatils
class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    success_url = reverse_lazy('product_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to perform this action.")
        return super().dispatch(request, *args, **kwargs)
    


# To remove the product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'shop/product_delete.html'
    success_url = reverse_lazy('product_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to perform this action.")
        return super().dispatch(request, *args, **kwargs)
    


# about the compant
def about(request):
    return render(request, 'shop/about.html')



# To add the product in the cart
class AddToCartView(View):
    @method_decorator(login_required)
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                raise ValueError("Quantity must be at least 1.")
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid quantity."}, status=400)

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return redirect('cart_detail')


# To see the cart details
class CartDetailView(View):
    @method_decorator(login_required)
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        return render(request, 'shop/cart_detail.html', {
            'cart': cart,
            'cart_items': cart_items,
            'total_price': total_price
        })

    @method_decorator(login_required)
    def post(self, request):
        # Process the checkout (mock payment)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()
        total_price = sum(item.product.price * item.quantity for item in cart_items)

        # Simulate payment
        payment_status = "Paid"

        # Create a checkout record
        Checkout.objects.create(
            user=request.user,
            order_items=", ".join([f"{item.product.title} x {item.quantity}" for item in cart_items]),
            total_price=total_price,
            payment_status=payment_status
        )

        # Clear the cart after checkout
        cart_items.delete()

        return redirect('address_details')



# change in the quantity of a product in the cart
class UpdateCartQuantityView(View):
    @method_decorator(login_required)
    def post(self, request, item_id, action):
        """
        Update the quantity of a cart item based on the action: 'increase' or 'decrease'.

        Args:
            item_id: The ID of the cart item to be updated.
            action: The action to perform ('increase' or 'decrease').

        Returns:
            Redirects to the cart details page.
        """
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

        return redirect('cart_detail')



# to buy the product
class CheckoutView(View):
    @method_decorator(login_required)
    def get(self, request):
        # If the user is logged in, redirect them to the address details page
        return redirect('address_details')

    @method_decorator(login_required)
    def post(self, request):
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        # If the cart is empty, redirect to the cart page
        if not cart_items.exists():
            return redirect('cart_detail')

        # After filling in the address, simulate successful payment
        payment_status = "Paid"

        # Create the checkout entry
        Checkout.objects.create(
            user=request.user,
            order_items=", ".join([f"{item.product.title} x {item.quantity}" for item in cart_items]),
            total_price=cart.get_total_price(),
            payment_status=payment_status
        )

        # Empty the cart after successful checkout
        cart_items.delete()

        # Redirect to the success page after payment
        return redirect('checkout_success')

# Step 2: Address details view
class AddressDetailsView(View):
    @method_decorator(login_required)
    def get(self, request):
        # Render the form for address details (if the user already has an address, pre-fill the form)
        address = Address.objects.filter(user=request.user).first()
        return render(request, 'shop/address_details.html', {'address': address})

    @method_decorator(login_required)
    def post(self, request):
        # Handle form submission and save address details
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        
        # Check if the user already has an address
        user_address, created = Address.objects.get_or_create(user=request.user)
        user_address.first_name = first_name
        user_address.last_name = last_name
        user_address.address = address
        user_address.phone_number = phone_number
        user_address.save()

        # Redirect to the payment page after address is entered
        return redirect('payment')

# Step 3: Payment view
class PaymentView(View):
    @method_decorator(login_required)
    def get(self, request):
        # Render the payment page (you can provide a message that COD is selected)
        return render(request, 'shop/payment.html')

    @method_decorator(login_required)
    def post(self, request):
        # Simulate Cash on Delivery (COD) payment status
        payment_status = "Cash on Delivery"  # Simulate COD payment

        # Get the user's cart and process the checkout
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()

        # If the cart is empty, redirect to the homepage (optional)
        if not cart_items.exists():
            return redirect('home')  # Or to another relevant page (e.g., 'cart_detail')

        # Create the checkout record with payment status as COD
        Checkout.objects.create(
            user=request.user,
            order_items=", ".join([f"{item.product.title} x {item.quantity}" for item in cart_items]),
            total_price=cart.get_total_price(),
            payment_status=payment_status
        )

        # Empty the cart after successful checkout
        cart_items.delete()

        # Redirect to the success page after successful COD order
        return redirect('checkout_success')
# Order History View to see past orders
@method_decorator(login_required, name='dispatch')
class OrderHistoryView(View):
    def get(self, request):
        # Retrieve past orders for the user
        orders = Checkout.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'shop/order_history.html', {'orders': orders})

# Successful payment
@login_required
def checkout_success_view(request):
    return render(request, 'shop/checkout_success.html')
