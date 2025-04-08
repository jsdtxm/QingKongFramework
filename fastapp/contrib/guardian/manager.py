from tortoise.transactions import in_transaction

from fastapp import models
from fastapp.contrib.auth.models import Permission
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.contrib.guardian.exceptions import ObjectNotPersisted
from fastapp.contrib.guardian.shortcuts import get_objects_for_group, get_objects_for_user
from fastapp.models import QuerySet
from fastapp.models.base import MODEL


class BaseObjectPermissionManager(models.Manager[MODEL]):
    @property
    def user_or_group_field(self):
        if "user" in self._model._meta.fields_map:
            return "user"
        return "group"

    async def assign_perm(self, perm: str, user_or_group, obj: models.Model):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.
        """

        if getattr(obj, "pk", None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first" % obj)

        ctype = await ContentType.from_model(obj)

        if not isinstance(perm, Permission):
            permission = Permission.objects.get(content_type=ctype, perm=perm)
        else:
            permission = perm

        kwargs = {
            "permission": permission,
            self.user_or_group_field: user_or_group,
            "content_type": ctype,
            "object_pk": obj.pk,
        }

        obj_perm, _ = self.get_or_create(**kwargs)
        return obj_perm

    async def bulk_assign_perm(self, perm, user_or_group, queryset: QuerySet):
        """
        Bulk assigns permissions with given ``perm`` for an objects in ``queryset`` and
        ``user_or_group``.
        """

        if isinstance(queryset, list):
            klass = queryset[0].__class__
        else:
            klass = queryset.model

        ctype = await ContentType.from_model(klass)

        if not isinstance(perm, Permission):
            permission = await Permission.objects.get(content_type=ctype, perm=perm)
        else:
            permission = perm

        async with in_transaction(self._model._meta.app_config.default_connection):
            pass

        if self.user_or_group_field == "user":
            assigned_objects = await get_objects_for_user(
                user_or_group,
                perm,
                klass,
                use_groups=False,
                with_superuser=False,
                accept_model_perms=False,
            )
        else:
            assigned_objects = await get_objects_for_group(
                user_or_group, perm, klass, accept_model_perms=False
            )

        existed_ids = await assigned_objects.values_list("id", flat=True)

        if isinstance(queryset, list):
            existed_ids_set = set(existed_ids)
            queryset = [x for x in queryset if x.id not in existed_ids_set]
        else:
            queryset = await queryset.exclude(pk__in=existed_ids)

        assigned_perms = []
        for instance in queryset:
            kwargs = {
                "permission": permission,
                self.user_or_group_field: user_or_group,
                "content_type": ctype,
                "object_id": instance.pk,
            }
            assigned_perms.append(self._model(**kwargs))

        await self._model.bulk_create(assigned_perms)

        return assigned_perms
