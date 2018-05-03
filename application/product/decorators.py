from flask import flash, abort

def admin_required(original_function):
    def wrapper_function(*args, **kwargs):
        user = kwargs.get('user')
        if user.role_name == 'Admin':
            original_function()
        else:
            flash('The logged in user doesn\'t have the permission to perform this operation', 'error')
            abort(403)
    #end of wrapper
    return wrapper_function
#end of func()