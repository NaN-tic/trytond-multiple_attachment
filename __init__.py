# This file is part of the multiple_attachment module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import attachment


def register():
    Pool.register(
        attachment.MultipleAttachment,
        attachment.MultipleAttachmentWizardStart,
        module='multiple_attachment', type_='model')
    Pool.register(
        attachment.MultipleAttachmentWizard,
        module='multiple_attachment', type_='wizard')
