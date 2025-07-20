from fastapp.models.fields import DateField, DateTimeField, RelationalField


def ger_full_fields_map(
    model,
    include_backward: bool = False,
    include_m2m: bool = True,
    include_auto: bool = True,
    include_fk_id: bool = True,
):
    fields_map = model._meta.fields_map

    if not include_backward:
        field_set = model._meta.backward_fk_fields | model._meta.backward_o2o_fields

        fields_map = {k: v for k, v in fields_map.items() if k not in field_set}

    if not include_m2m:
        fields_map = {
            k: v for k, v in fields_map.items() if k not in model._meta.m2m_fields
        }

    if not include_auto:
        fields_map = {
            k: v
            for k, v in fields_map.items()
            if not v.generated
            and not (
                (isinstance(v, DateTimeField) or isinstance(v, DateField))
                and (v.auto_now or v.auto_now_add)
            )
        }

    if not include_fk_id:
        fk_id_field_set = {f"{x}_id" for x in model._meta.fk_fields}
        fields_map = {k: v for k, v in fields_map.items() if k not in fk_id_field_set}

    return fields_map


def get_verbose_name_dict(fields_map: dict, extra_verbose_name_dict=None):
    """get_verbose_name_dict"""

    res = {}
    extra_verbose_name_dict = extra_verbose_name_dict or {}

    for k, v in fields_map.items():
        verbose_name = getattr(v, "verbose_name", None) or extra_verbose_name_dict.get(
            k, k
        )
        if verbose_name and verbose_name != k:
            res[k] = verbose_name
            if isinstance(v, RelationalField):
                res[f"{k}_id"] = f"{verbose_name}ID"
                for sk, sv in v.related_model._meta.fields_map.items():
                    sub_verbose_name = getattr(
                        sv, "verbose_name", None
                    ) or extra_verbose_name_dict.get(sk, sk)
                    res[f"{k}.{sk}"] = f"{verbose_name}.{sub_verbose_name}"

    return res


def get_verbose_name_dict_nesting(fields_map: dict, extra_verbose_name_dict=None):
    """get_verbose_name_dict_nesting"""

    res = {}
    extra_verbose_name_dict = extra_verbose_name_dict or {}

    for k, v in fields_map.items():
        verbose_name = getattr(v, "verbose_name", None) or extra_verbose_name_dict.get(
            k, k
        )
        if verbose_name and verbose_name != k:
            res[k] = {
                "verbose_name": verbose_name,
            }
            if isinstance(v, RelationalField):
                res[f"{k}_id"] = {
                    "verbose_name": f"{verbose_name}ID",
                }
                for sk, sv in v.related_model._meta.fields_map.items():
                    sub_verbose_name = getattr(
                        sv, "verbose_name", None
                    ) or extra_verbose_name_dict.get(sk, sk)
                    if "children" not in res[k]:
                        res[k]["children"] = {}
                    res[k]["children"][sk] = {
                        "verbose_name": sub_verbose_name,
                    }

    return res
