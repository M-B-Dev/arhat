import json

from flask import (
    Response,
    current_app,
    redirect,
    request,
    url_for,
)
from flask_login import current_user

from app import db
from app.sub import bp
from app.models import User


@bp.route("/subscribe/", methods=["GET", "POST"])
def subscribe():
    """Gets and stores a user notification subscription in the db."""
    subscription = request.json.get("sub_token")
    User.query.all()[0].subscription = json.dumps(subscription)
    db.session.commit()
    return redirect(url_for("sn.edit_profile"))


@bp.route("/subscription/", methods=["GET", "POST"])
def subscription():
    """
    returns vapid public key which clients uses
    to send around push notification.
    """

    if request.method == "GET":
        return Response(
            response=json.dumps({"public_key": current_app.config["VAPID_PUBLIC_KEY"]}),
            headers={"Access-Control-Allow-Origin": "*"},
            content_type="application/json",
        )
    subscription_token = request.get_json("subscription_token")    
    return Response(status=201, mimetype="application/json")


@bp.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
    """turns off user notifications."""
    current_user.subscribed = False
    current_user.subscription = None
    db.session.commit()
    return redirect(url_for("main.index", date_set="ph"))


@bp.route("/sub", methods=["GET", "POST"])
def flask_subscribe():
    """Sets user notifications to off in the database."""
    if not current_user.subscribed:
        current_user.subscribed = True
    else:
        current_user.subscribed = False
    db.session.commit()
    return redirect(url_for("sn.edit_profile"))