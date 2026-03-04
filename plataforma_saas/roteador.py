from plataforma_saas.tenant import obter_alias_banco


class RoteadorTenant:
    apps_central = {"core"}
    apps_tenant = {"crm"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.apps_tenant:
            return obter_alias_banco()
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.apps_tenant:
            return obter_alias_banco()
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.apps_central:
            return db == "default"
        if app_label in self.apps_tenant:
            return db != "default"
        return None
