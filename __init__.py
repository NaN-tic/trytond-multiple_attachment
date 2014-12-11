# This file is part of the multiple_attachment module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .attachment import *


def register():
    Pool.register(
        MultipleAttachment,
        MultipleAttachmentWizardStart,
        module='multiple_attachment', type_='model')
    Pool.register(
        MultipleAttachmentWizard,
        module='multiple_attachment', type_='wizard')
