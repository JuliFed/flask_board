class User:
    def __init__(self, json_user):
        if json_user:
            self.id = str(json_user['_id'])
            self.username = json_user['login']
            self.password = json_user['password']

    def __str__(self):
        return "User(id='%s')" % self.id


