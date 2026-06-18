from django.core.validators import ValidationError

import cvss


def CvssValidator(value):
    try:
        cvss.CVSS3(value).base_score
    except Exception as e:
        raise ValidationError("Not a valid CVSS vector: {}".format(e))
