# This file is part of the multiple_attachment module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from lxml import etree
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.wizard import Button, StateView, StateTransition, Wizard


__all__ = ['MultipleAttachment', 'MultipleAttachmentWizardStart',
    'MultipleAttachmentWizard']


class MultipleAttachment(ModelSQL, ModelView):
    'Multiple Attachment'
    __name__ = 'multiple.attachment'
    model = fields.Many2One('ir.model', 'Model', required=True)
    keyword = fields.Many2One('ir.action.keyword', 'Wizard', readonly=True)

    @classmethod
    def __setup__(cls):
        super(MultipleAttachment, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('model_uniq', Unique(t, t.model),
                'Multiple Attachment must be unique per model.'),
        ]
        cls._error_messages.update({
                'not_modelsql': 'Model "%s" does not store information '
                    'to an SQL table.',
                })
        cls._buttons.update({
                'create_wizard': {
                    'invisible': Eval('keyword'),
                    },
                'remove_wizard': {
                    'invisible': ~Eval('keyword'),
                    },
                })

    @classmethod
    def validate(cls, multi_attachments):
        super(MultipleAttachment, cls).validate(multi_attachments)
        for multi_attachment in multi_attachments:
            Model = Pool().get(multi_attachment.model.model)
            if not issubclass(Model, ModelSQL):
                cls.raise_user_error('not_modelsql',
                    (multi_attachment.model.rec_name,))

    @classmethod
    @ModelView.button
    def create_wizard(cls, multi_attachments):
        pool = Pool()
        Action = pool.get('ir.action.wizard')
        ModelData = pool.get('ir.model.data')
        Keyword = pool.get('ir.action.keyword')

        for multi_attachment in multi_attachments:
            if multi_attachment.keyword:
                continue
            action = Action(ModelData.get_id('multiple_attachment',
                    'wizard_multiple_attachment'))
            keyword = Keyword()
            keyword.keyword = 'form_action'
            keyword.model = '%s,-1' % multi_attachment.model.model
            keyword.action = action.action
            keyword.save()
            multi_attachment.keyword = keyword
            multi_attachment.save()

    @classmethod
    @ModelView.button
    def remove_wizard(cls, multi_attachments):
        pool = Pool()
        Keyword = pool.get('ir.action.keyword')
        Keyword.delete([x.keyword for x in multi_attachments if x.keyword])

    @classmethod
    def delete(cls, multi_attachments):
        cls.remove_wizard(multi_attachments)
        super(MultipleAttachment, cls).delete(multi_attachments)


class MultipleAttachmentWizardStart(ModelView):
    'Multiple Attachment Wizard Start'
    __name__ = 'multiple.attachment.wizard.start'

    @classmethod
    def get_attributes_for_field_attachment(cls, attachment_model,
            active_id):
        return {
            'type': 'many2one',
            'name': 'attachment',
            'relation': 'ir.attachment',
            'string': 'Attachment',
            'required': True,
            'domain': [
                ('resource', 'like', (attachment_model + ',%')),
                ],
            'context': {
                'resource': '%s,%s' % (attachment_model, active_id),
                }
            }

    @classmethod
    def get_attributes_for_field_records(cls, attachment_model):
        return {
            'type': 'one2many',
            'name': 'records',
            'relation': attachment_model,
            'field': None,
            'string': 'Records',
            'required': True,
            }

    @classmethod
    def fields_view_get(cls, view_id=None, view_type='form'):
        pool = Pool()
        View = pool.get('ir.ui.view')
        attachment_view, = View.search([
                ('model', '=', 'ir.attachment'),
                ('type', '=', 'tree'),
                ('module', '=', 'multiple_attachment'),
                ])
        res = super(MultipleAttachmentWizardStart, cls).fields_view_get(
            view_id, view_type)
        context = Transaction().context
        model = context.get('active_model', None)
        active_id = context.get('active_id', None)
        if not model:
            return res
        AttachmentModel = pool.get(model)
        attachment_model = AttachmentModel.__name__
        root = etree.fromstring(res['arch'])
        form = root.find('separator').getparent()
        etree.SubElement(form, 'label', {
                'name': 'attachment',
                'colspan': '2',
                })
        etree.SubElement(form, 'field', {
                'name': 'attachment',
                'colspan': '2',
                'view_ids': '%s' % attachment_view.id,
                })
        etree.SubElement(form, 'field', {
                'name': 'records',
                'colspan': '4',
                })
        res['arch'] = etree.tostring(root)
        res['fields'].update({
                'attachment':
                    cls.get_attributes_for_field_attachment(attachment_model,
                        active_id),
                'records':
                    cls.get_attributes_for_field_records(attachment_model),
                })
        return res

    @classmethod
    def default_get(cls, fields, with_rec_name=True):
        context = Transaction().context
        active_ids = context.get('active_ids', None)
        res = {
            'records': active_ids,
            }
        return res


class MultipleAttachmentWizard(Wizard):
    'Multiple Attachment Wizard'
    __name__ = 'multiple.attachment.wizard'
    start = StateView('multiple.attachment.wizard.start',
        'multiple_attachment.view_multiple_attachment_wizard_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Attach', 'attach', 'tryton-ok', True),
            ])
    attach = StateTransition()

    def transition_attach(self):
        'Regenerates all actions and wizard entries'
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        context = Transaction().context
        active_ids = context.get('active_ids', None)
        model = context['active_model']

        attachment = Attachment(self.start.attachment)
        for active_id in active_ids:
            if str(attachment.resource) != '%s,%s' % (model, active_id):
                default_values = {
                    'resource': '%s,%s' % (model, active_id),
                    }
                attachment, = Attachment.copy([attachment], default_values)
                attachment.save()
        return 'end'
