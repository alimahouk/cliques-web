from app import app, socketio
from routing import admin, errors, json, sockets, web


@app.route("/admin", methods=["GET"])
def admin_console():
        return admin.console()


@app.route("/admin/comments/erase", methods=["POST"])
def admin_comment_erase():
        return admin.comment_erase()


@app.route("/admin/posts/erase", methods=["POST"])
def admin_post_erase():
        return admin.post_erase()


@app.route("/admin/threads/erase", methods=["POST"])
def admin_thread_erase():
        return admin.thread_erase()

@app.route("/admin/threads/ghost", methods=["POST"])
def admin_thread_ghost():
        return admin.thread_ghost()


@app.route("/admin/threads/lock", methods=["POST"])
def admin_thread_lock():
        return admin.thread_lock()


@app.route("/admin/threads/modify", methods=["POST"])
def admin_thread_modify():
        return admin.thread_modify()


@app.route("/admin/users/delete", methods=["POST"])
def admin_user_delete():
        return admin.user_delete()


@app.route("/admin/users/update", methods=["POST"])
def admin_user_update():
        return admin.user_update()


@app.route("/admin/users/suspend", methods=["POST"])
def admin_user_suspend():
        return admin.user_suspend()


###############################################################################


@app.route("/api/threads/clique/get", methods=["POST"])
def api_clique_threads_get():
        return json.clique_threads_get()


@app.route("/api/threads/clique/make", methods=["POST"])
def api_clique_thread_make():
        return json.clique_thread_make()


@app.route("/api/threads/clique/mark", methods=["POST"])
def api_clique_threads_mark_read():
        return json.clique_threads_mark_read()


@app.route("/api/cliques/get", methods=["POST"])
def api_cliques_get():
        return json.cliques_get()


@app.route("/api/comments/make", methods=["POST"])
def api_comment_make():
        return json.comment_make()


@app.route("/api/comments/get", methods=["POST"])
def api_comments_get():
        return json.comments_get()


@app.route("/api/connections/remove", methods=["POST"])
def api_connection_remove():
        return json.connection_remove()


@app.route("/api/connections/requests/accept", methods=["POST"])
def api_connection_request_accept():
        return json.connection_request_accept()


@app.route("/api/connections/requests/decline", methods=["POST"])
def api_connection_request_decline():
        return json.connection_request_decline()


@app.route("/api/connections/requests/make", methods=["POST"])
def api_connection_request_make():
        return json.connection_request_make()


@app.route("/api/connections/requests/revoke", methods=["POST"])
def api_connection_request_revoke():
        return json.connection_request_revoke()


@app.route("/api/connections/requests/received/get", methods=["POST"])
def api_connection_requests_received_get():
        return json.connection_requests_received_get()


@app.route("/api/connections/requests/received/mark", methods=["POST"])
def api_connection_requests_received_mark():
        return json.connection_requests_received_mark()


@app.route("/api/connections/requests/sent/get", methods=["POST"])
def api_connection_requests_sent_get():
        return json.connection_requests_sent_get()


@app.route("/api/connections/get", methods=["POST"])
def api_connections_get():
        return json.connections_get()


@app.route("/api/connections/invite/make", methods=["POST"])
def api_invite_link_make():
        return json.invite_link_make()


@app.route("/api/login", methods=["POST"])
def api_login():
        return json.login()


@app.route("/api/lr/get", methods=["POST"])
def api_lr_all_get():
        return json.lr_all_get()


@app.route("/api/threads/lr/make", methods=["POST"])
def api_lr_thread_make():
        return json.lr_thread_make()


@app.route("/api/threads/lr/get", methods=["POST"])
def api_lr_threads_get():
        return json.lr_threads_get()


@app.route("/api/threads/lr/mark", methods=["POST"])
def api_lr_threads_mark_read():
        return json.lr_threads_mark_read()


@app.route("/api/posts/make", methods=["POST"])
def api_post_make():
        return json.post_make()


@app.route("/api/posts/get", methods=["POST"])
def api_posts_get():
        return json.posts_get()


@app.route("/api/threads/get", methods=["POST"])
def api_thread_get():
        return json.thread_get()


###############################################################################


@app.route("/clique", methods=["GET"])
def web_clique():
        return web.clique()


@app.route("/connections/accept", methods=["POST"])
def web_connection_accept():
        return web.connection_accept()


@app.route("/connections/add", methods=["GET", "POST"])
def web_connection_add():
        return web.connection_add()


@app.route("/connections/remove", methods=["POST"])
def web_connection_remove():
        return web.connection_remove()


@app.route("/connections/requests", methods=["GET"])
def web_connection_requests():
        return web.connection_requests()


@app.route("/connections", methods=["GET"])
def web_connections():
        return web.connections()


@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def web_index():
        return web.index()


@app.route("/login", methods=["GET", "POST"])
def web_login():
        return web.login()


@app.route("/logout", methods=["GET"])
def web_logout():
        return web.logout()


@app.route('/lr', defaults={"country": None}, methods=["GET"])
@app.route("/lr/<country>", methods=["GET"])
def web_lr(country):
        return web.lr(country)


@app.route("/lr/list", methods=["GET"])
def web_lr_list():
        return web.lr_list()


@app.route('/forgot', methods=["GET", "POST"])
def web_password_forgot():
        return web.password_forgot()


@app.route('/passwordreset', methods=["POST"])
def web_password_reset():
        return web.password_reset()


@app.route('/submit/post', methods=["POST"])
def web_submit_post():
        return web.submit_post()


@app.route('/submit/thread', methods=["GET", "POST"])
def web_submit_thread():
        return web.submit_thread()


@app.route('/scape', methods=["GET"])
def web_scape():
        return web.scape()


@app.route("/signup", methods=["GET", "POST"])
def web_signup():
        return web.signup()


@app.route("/", subdomain="about", methods=["GET"])
def web_about():
        return web.about()


@app.route("/community", subdomain="about", methods=["GET"])
def web_community():
        return web.community()


@app.route("/contact", subdomain="about", methods=["GET", "POST"])
def web_contact():
        return web.contact()


@app.route("/privacy", subdomain="about", methods=["GET"])
def web_privacy():
        return web.privacy()


@app.route("/terms", subdomain="about", methods=["GET"])
def web_tos():
        return web.tos()


###############################################################################


@app.errorhandler(400)
def err_bad_request(e):
        return errors.bad_request(e)


@app.errorhandler(401)
def err_auth_required(e):
        return errors.auth_required(e)


@app.errorhandler(403)
def err_forbidden(e):
        return errors.forbidden(e)


@app.errorhandler(404)
def err_page_not_found(e):
        return errors.page_not_found(e)


###############################################################################


@socketio.on("connect")
def socket_connected():
        return sockets.connected()


@socketio.on("disconnect")
def socket_disconnected():
        sockets.disconnected()


@socketio.on("message")
def socket_handle_message(message):
        sockets.handle_message(message)
