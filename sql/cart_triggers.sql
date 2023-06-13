delimiter |
CREATE TRIGGER cart_add_item BEFORE INSERT ON client_cart_item
    FOR EACH ROW
    BEGIN
        UPDATE client_cart SET client_cart.cart_subtotal = client_cart.cart_subtotal + (NEW.quantity * NEW.price)
        WHERE client_cart.id=NEW.cart_id;
        UPDATE client_cart SET client_cart.cart_tax = client_cart.cart_tax + IF(ISNULL(NEW.net_tax), 0, NEW.net_tax)
        WHERE client_cart.id=NEW.cart_id;
        UPDATE client_cart SET client_cart.cart_total = IF(client_cart.cart_subtotal > 0, client_cart.cart_subtotal + client_cart.cart_tax, 0)
        WHERE client_cart.id=NEW.cart_id;
    END;
|

CREATE TRIGGER cart_update_item BEFORE UPDATE ON client_cart_item
    FOR EACH ROW
    BEGIN
        UPDATE client_cart SET client_cart.cart_subtotal = client_cart.cart_subtotal - (OLD.quantity * OLD.price)
        WHERE client_cart.id=OLD.cart_id;
        UPDATE client_cart SET client_cart.cart_subtotal = client_cart.cart_subtotal + (NEW.quantity * NEW.price)
        WHERE client_cart.id=NEW.cart_id;
        UPDATE client_cart SET client_cart.cart_tax = client_cart.cart_tax - IF(ISNULL(OLD.net_tax), 0, OLD.net_tax)
        WHERE client_cart.id=OLD.cart_id;
        UPDATE client_cart SET client_cart.cart_tax = client_cart.cart_tax + IF(ISNULL(NEW.net_tax), 0, NEW.net_tax)
        WHERE client_cart.id=NEW.cart_id;
        UPDATE client_cart SET client_cart.cart_total = IF(client_cart.cart_subtotal > 0, client_cart.cart_subtotal + client_cart.cart_tax, 0)
        WHERE client_cart.id=NEW.cart_id;
    END;
|

CREATE TRIGGER cart_delete_item BEFORE DELETE ON client_cart_item
    FOR EACH ROW
    BEGIN
        UPDATE client_cart SET client_cart.cart_subtotal = client_cart.cart_subtotal - (OLD.quantity * OLD.price)
        WHERE client_cart.id=OLD.cart_id;
        UPDATE client_cart SET client_cart.cart_tax = client_cart.cart_tax - IF(ISNULL(OLD.net_tax), 0, OLD.net_tax)
        WHERE client_cart.id=OLD.cart_id;
        UPDATE client_cart SET client_cart.cart_total = IF(client_cart.cart_subtotal > 0, client_cart.cart_subtotal + client_cart.cart_tax, 0)
        WHERE client_cart.id=OLD.cart_id;
    END;

|
delimiter ;

