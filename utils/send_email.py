def send_admin_email(subject, order):
    # TODO: Implement email sendingc
    email_body = f"""
        New Order Placed!

        Order ID: #{order.id}
        Customer: {order.customer.first_name} {order.customer.last_name}
        Email: {order.customer.email}
        Phone: {order.customer.phone}
        Total Amount: ${order.total_amount}
        Order Date: {order.order_date}

        Items:
        """

    for item in order.items.all():
        email_body += f"- {item.quantity}x {item.product.name} @ ${item.unit_price} = ${item.total_price}\n"

    if order.notes:
        email_body += f"\nNotes: {order.notes}"

    print(f"Email Subject: {subject}")
    print(f"Email Body: {email_body}")
    pass