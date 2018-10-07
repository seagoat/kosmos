# Create your tasks here
from __future__ import absolute_import, unicode_literals

import os
import zipfile

from celery import shared_task
from celery.utils.log import get_task_logger
from dateutil import parser
from django.core.files import File
from django.utils.timezone import make_aware

from .models import Address, Attachment, Category, Email, KosmosError, Meeting
from .xml_parser import emails

log = get_task_logger(__name__)


def parse_address(address):
    result = {}

    result['address'] = address.get_OPFContactEmailAddressAddress()
    if result['address'] is None:
        result['address'] = ''
    result['name'] = address.get_OPFContactEmailAddressName()
    if result['name'] is None:
        result['name'] = ''
    result['content_type'] = address.get_OPFContactEmailAddressType()
    if result['content_type'] is None:
        result['content_type'] = ''

    return result


def parse_addresses(addresses):
    results = []

    if addresses:
        for address in addresses.get_emailAddress():
            result = parse_address(address)
            results.append(result)

    return results


@shared_task
def parse_olm_dirs(olm_dirs):
    for root, _, files in os.walk(olm_dirs):
        for filename in files:
            olm_filename = os.path.join(root, filename)
            if not filename.lower().endswith('.olm'):
                log.info('Skip NOT OLM file: [{}]'.format(olm_filename))
                continue
            log.info('Parsing OLM: [{}]'.format(olm_filename))
            parse_olm.delay(olm_filename)


@shared_task
def parse_olm(olm_filename):
    with zipfile.ZipFile(olm_filename, mode='r', allowZip64=True) as zf:
        olm_item_urls = zf.namelist()

    log.info('{} items in {}'.format(len(olm_item_urls), olm_filename))
    for olm_item_url in olm_item_urls:
        parse_olm_item(olm_filename, olm_item_url)


@shared_task
def parse_olm_item(olm_filename, olm_item_url):
    msg = ''
    dirs = olm_item_url.split('/')

    if olm_item_url.endswith('/'):
        msg = 'Skip directory: [{}]'.format(olm_item_url)
        log.debug(msg)
        return True

    if len(dirs) <= 1:
        msg = 'Skip root: [{}]'.format(olm_item_url)
        log.debug(msg)
        return True
    elif dirs[-1] == 'Contacts.xml':
        log.warning(olm_item_url)
        # parse_contacts.delay(olm_filename, olm_item_url)
        return True

    elif dirs[-1] == 'Calendar.xml':
        log.warning(olm_item_url)
        # parse_calendar.delay(olm_filename, olm_item_url)
        return True

    elif dirs[1] == 'com.microsoft.__Messages':
        if dirs[3] == 'com.microsoft.__Attachments':
            msg = 'Skip attchement file: [{}]'.format(olm_item_url)
            log.debug(msg)
            return True

        if not olm_item_url.lower().endswith('.xml'):
            msg = 'Skip not xml file: [{}]'.format(olm_item_url)
            log.error(msg)
            return True

        log.debug('Parsing email xml: [{}]'.format(olm_item_url))
        parse_email.delay(olm_filename, olm_item_url)

        return True

    else:
        msg = 'Unsupported xml file: [{}]'.format(olm_item_url)
        log.warning(msg)
        return False


def export_fileobj_to_django(olm_filename, olm_item_url, django_cls):
    django_obj, created = django_cls.objects.get_or_create(
        olm_filename=olm_filename,
        olm_item_url=olm_item_url,
    )

    if not created:
        return django_obj

    with zipfile.ZipFile(olm_filename, mode='r', allowZip64=True) as zf:
        with zf.open(olm_item_url) as zip_data:
            django_obj.file_obj = File(zip_data)
            django_obj.save()

    return django_obj


@shared_task
def record_error(olm_filename, olm_item_url):

    return export_fileobj_to_django(olm_filename, olm_item_url, KosmosError).id
    # kosmos_error, created = KosmosError.objects.get_or_create(
    #     olm_filename=olm_filename,
    #     olm_item_url=olm_item_url,
    # )

    # if not created:
    #     return kosmos_error.id

    # with zipfile.ZipFile(olm_filename, mode='r', allowZip64=True) as zf:
    #     with zf.open(olm_item_url) as xml_item:
    #         kosmos_error.file_obj = File(xml_item)
    #         kosmos_error.save()

    # return kosmos_error.id


@shared_task
def parse_calendar(olm_filename, olm_item_url):
    record_error.delay(olm_filename, olm_item_url)
    return False


@shared_task
def parse_contacts(olm_filename, olm_item_url):
    record_error.delay(olm_filename, olm_item_url)
    return False


@shared_task
def parse_email(olm_filename, olm_item_url):

    with zipfile.ZipFile(olm_filename, mode='r', allowZip64=True) as zf:
        with zf.open(olm_item_url) as xml_item:
            try:
                _emails = emails.parse(xml_item, silence=True)
            except:
                log.error('Failed to decode xml[{}|{}]'.format(
                    olm_filename, olm_item_url))

                record_error.delay(olm_filename, olm_item_url)
                return False

            for email in _emails.get_email():
                result = {}
                result['olm_filename'] = olm_filename
                result['olm_item_url'] = olm_item_url

                # def get_OPFMessageCopyMessageID(self): return self.OPFMessageCopyMessageID
                # def set_OPFMessageCopyMessageID(self, OPFMessageCopyMessageID): self.OPFMessageCopyMessageID = OPFMessageCopyMessageID
                if email.get_OPFMessageCopyMessageID():
                    message_id = email.get_OPFMessageCopyMessageID().get_valueOf_()
                    result['message_id'] = message_id
                    log.debug('message_id:[{}]'.format(message_id))
                    # assert(0)

                # def get_OPFMessageCopyThreadTopic(self): return self.OPFMessageCopyThreadTopic
                # def set_OPFMessageCopyThreadTopic(self, OPFMessageCopyThreadTopic): self.OPFMessageCopyThreadTopic = OPFMessageCopyThreadTopic
                if email.get_OPFMessageCopyThreadTopic():
                    thread_topic = email.get_OPFMessageCopyThreadTopic().get_valueOf_()
                    result['thread_topic'] = thread_topic
                    log.debug('thread_topic:[{}]'.format(thread_topic))

                # def get_OPFMessageCopySubject(self): return self.OPFMessageCopySubject
                # def set_OPFMessageCopySubject(self, OPFMessageCopySubject): self.OPFMessageCopySubject = OPFMessageCopySubject
                if email.get_OPFMessageCopySubject():
                    subject = email.get_OPFMessageCopySubject().get_valueOf_()
                    result['subject'] = subject
                    log.debug('subject:[{}]'.format(subject))
                    # assert(0)

                # def get_OPFMessageCopyThreadIndex(self): return self.OPFMessageCopyThreadIndex
                # def set_OPFMessageCopyThreadIndex(self, OPFMessageCopyThreadIndex): self.OPFMessageCopyThreadIndex = OPFMessageCopyThreadIndex
                if email.get_OPFMessageCopyThreadIndex():
                    thread_index = email.get_OPFMessageCopyThreadIndex().get_valueOf_()
                    result['thread_index'] = thread_index
                    log.debug(
                        'thread_index:[{}]'.format(thread_index))

                # def get_OPFMessageCopyReceivedTime(self): return self.OPFMessageCopyReceivedTime
                # def set_OPFMessageCopyReceivedTime(self, OPFMessageCopyReceivedTime): self.OPFMessageCopyReceivedTime = OPFMessageCopyReceivedTime
                if email.get_OPFMessageCopyReceivedTime():
                    received_time = make_aware(parser.parse(
                        email.get_OPFMessageCopyReceivedTime().get_valueOf_()))
                    result['received_time'] = received_time
                    log.debug('received_time:[{}]'.format(received_time))

                # def get_OPFMessageCopySentTime(self): return self.OPFMessageCopySentTime
                # def set_OPFMessageCopySentTime(self, OPFMessageCopySentTime): self.OPFMessageCopySentTime = OPFMessageCopySentTime
                if email.get_OPFMessageCopySentTime():
                    sent_time = make_aware(parser.parse(
                        email.get_OPFMessageCopySentTime().get_valueOf_()))
                    result['sent_time'] = sent_time
                    log.debug('sent_time:[{}]'.format(sent_time))

                # def get_OPFMessageCopyCompletedDateTime(self): return self.OPFMessageCopyCompletedDateTime
                # def set_OPFMessageCopyCompletedDateTime(self, OPFMessageCopyCompletedDateTime): self.OPFMessageCopyCompletedDateTime = OPFMessageCopyCompletedDateTime
                if email.get_OPFMessageCopyCompletedDateTime():
                    completed_datetime = make_aware(parser.parse(
                        email.get_OPFMessageCopyCompletedDateTime().get_valueOf_()))
                    result['completed_datetime'] = completed_datetime
                    log.debug('completed_datetime:[{}]'.format(
                        completed_datetime))

                # def get_OPFMessageCopyDueDateTime(self): return self.OPFMessageCopyDueDateTime
                # def set_OPFMessageCopyDueDateTime(self, OPFMessageCopyDueDateTime): self.OPFMessageCopyDueDateTime = OPFMessageCopyDueDateTime
                if email.get_OPFMessageCopyDueDateTime():
                    due_datetime = make_aware(parser.parse(
                        email.get_OPFMessageCopyDueDateTime().get_valueOf_()))
                    result['due_datetime'] = due_datetime
                    log.debug('due_datetime:[{}]'.format(due_datetime))

                # def get_OPFMessageCopyStartDateTime(self): return self.OPFMessageCopyStartDateTime
                # def set_OPFMessageCopyStartDateTime(self, OPFMessageCopyStartDateTime): self.OPFMessageCopyStartDateTime = OPFMessageCopyStartDateTime
                if email.get_OPFMessageCopyStartDateTime():
                    start_datetime = make_aware(parser.parse(
                        email.get_OPFMessageCopyStartDateTime().get_valueOf_()))
                    result['start_datetime'] = start_datetime
                    log.debug('start_datetime:[{}]'.format(start_datetime))

                # def get_OPFMessageCopyModDate(self): return self.OPFMessageCopyModDate
                # def set_OPFMessageCopyModDate(self, OPFMessageCopyModDate): self.OPFMessageCopyModDate = OPFMessageCopyModDate
                if email.get_OPFMessageCopyModDate():
                    mod_date = make_aware(parser.parse(
                        email.get_OPFMessageCopyModDate().get_valueOf_()))
                    result['mod_date'] = mod_date
                    log.debug('mode_date:[{}]'.format(mod_date))

                # def get_OPFMessageCopyReminderDateTime(self): return self.OPFMessageCopyReminderDateTime
                # def set_OPFMessageCopyReminderDateTime(self, OPFMessageCopyReminderDateTime): self.OPFMessageCopyReminderDateTime = OPFMessageCopyReminderDateTime
                if email.get_OPFMessageCopyReminderDateTime():
                    reminder_datetime = make_aware(parser.parse(
                        email.get_OPFMessageCopyReminderDateTime().get_valueOf_()))
                    result['reminder_datetime'] = reminder_datetime
                    log.debug('reminder_datetime:[{}]'.format(
                        reminder_datetime))
                    assert(0)

                # def get_OPFMessageGetHasHTML(self): return self.OPFMessageGetHasHTML
                # def set_OPFMessageGetHasHTML(self, OPFMessageGetHasHTML): self.OPFMessageGetHasHTML = OPFMessageGetHasHTML
                if email.get_OPFMessageGetHasHTML():
                    has_html = bool(float(
                        email.get_OPFMessageGetHasHTML().get_valueOf_()))
                    log.debug('has_html:[{}]'.format(has_html))
                    result['has_html'] = has_html
                    # assert(0)

                # def get_OPFMessageCopyBody(self): return self.OPFMessageCopyBody
                # def set_OPFMessageCopyBody(self, OPFMessageCopyBody): self.OPFMessageCopyBody = OPFMessageCopyBody
                if email.get_OPFMessageCopyBody():
                    body = email.get_OPFMessageCopyBody().get_valueOf_()
                    log.debug('body:[{}]'.format(body))
                    result['body'] = body
                    # assert(0)

                # def get_OPFMessageCopyHTMLBody(self): return self.OPFMessageCopyHTMLBody
                # def set_OPFMessageCopyHTMLBody(self, OPFMessageCopyHTMLBody): self.OPFMessageCopyHTMLBody = OPFMessageCopyHTMLBody
                if email.get_OPFMessageCopyHTMLBody():
                    html_body = email.get_OPFMessageCopyHTMLBody().get_valueOf_()
                    log.debug('html_body:[{}]'.format(html_body))
                    result['html_body'] = html_body
                    # assert(0)

                # def get_OPFMessageCopyReferences(self): return self.OPFMessageCopyReferences
                # def set_OPFMessageCopyReferences(self, OPFMessageCopyReferences): self.OPFMessageCopyReferences = OPFMessageCopyReferences
                if email.get_OPFMessageCopyReferences():
                    references = email.get_OPFMessageCopyReferences().get_valueOf_()
                    result['references'] = references
                    log.debug('references:[{}]'.format(references))
                    # Todo: need implement reference process future
                    # assert(0)

                # def get_OPFMessageCopyInReplyTo(self): return self.OPFMessageCopyInReplyTo
                # def set_OPFMessageCopyInReplyTo(self, OPFMessageCopyInReplyTo): self.OPFMessageCopyInReplyTo = OPFMessageCopyInReplyTo
                if email.get_OPFMessageCopyInReplyTo():
                    replyto = email.get_OPFMessageCopyInReplyTo().get_valueOf_()
                    result['replyto'] = replyto
                    log.debug('replyto:[{}]'.format(replyto))
                    # Todo: need to check what is replyto
                    # assert(0)

                # def get_OPFMessageCopyReceivedRepresentingName(self): return self.OPFMessageCopyReceivedRepresentingName
                # def set_OPFMessageCopyReceivedRepresentingName(self, OPFMessageCopyReceivedRepresentingName): self.OPFMessageCopyReceivedRepresentingName = OPFMessageCopyReceivedRepresentingName
                if email.get_OPFMessageCopyReceivedRepresentingName():
                    receive_representing_name = email.get_OPFMessageCopyReceivedRepresentingName().get_valueOf_()
                    result['receive_representing_name'] = receive_representing_name
                    log.debug('receive_representing_name:[{}]'.format(
                        receive_representing_name))
                    assert(0)

                # def get_OPFMessageGetCalendarAcceptStatus(self): return self.OPFMessageGetCalendarAcceptStatus
                # def set_OPFMessageGetCalendarAcceptStatus(self, OPFMessageGetCalendarAcceptStatus): self.OPFMessageGetCalendarAcceptStatus = OPFMessageGetCalendarAcceptStatus
                if email.get_OPFMessageGetCalendarAcceptStatus():
                    calendar_accept_status = email.get_OPFMessageGetCalendarAcceptStatus().get_valueOf_()
                    result['calendar_accept_status'] = calendar_accept_status

                    log.debug('calendar_accept_status:[{}]'.format(
                        calendar_accept_status))

                # def get_OPFMessageGetSendReadReceipt(self): return self.OPFMessageGetSendReadReceipt
                # def set_OPFMessageGetSendReadReceipt(self, OPFMessageGetSendReadReceipt): self.OPFMessageGetSendReadReceipt = OPFMessageGetSendReadReceipt
                if email.get_OPFMessageGetSendReadReceipt():
                    send_read_receipt = email.get_OPFMessageGetSendReadReceipt().get_valueOf_()
                    result['send_read_receipt'] = send_read_receipt

                    log.debug('send_read_receipt:[{}]'.format(
                        send_read_receipt))

                # def get_OPFMessageGetMentionedMe(self): return self.OPFMessageGetMentionedMe
                # def set_OPFMessageGetMentionedMe(self, OPFMessageGetMentionedMe): self.OPFMessageGetMentionedMe = OPFMessageGetMentionedMe
                if email.get_OPFMessageGetMentionedMe():
                    mentioned_me = bool(
                        float(email.get_OPFMessageGetMentionedMe().get_valueOf_()))
                    result['mentioned_me'] = mentioned_me

                    log.debug('mentioned_me:[{}]'.format(mentioned_me))

                # def get_OPFMessageGetInferenceClassification(self): return self.OPFMessageGetInferenceClassification
                # def set_OPFMessageGetInferenceClassification(self, OPFMessageGetInferenceClassification): self.OPFMessageGetInferenceClassification = OPFMessageGetInferenceClassification
                if email.get_OPFMessageGetInferenceClassification():
                    inference_classfication = email.get_OPFMessageGetInferenceClassification().get_valueOf_()
                    result['inference_classfication'] = inference_classfication
                    log.debug('inference_classfication:[{}]'.format(
                        inference_classfication))

                # def get_OPFMessageGetHasRichText(self): return self.OPFMessageGetHasRichText
                # def set_OPFMessageGetHasRichText(self, OPFMessageGetHasRichText): self.OPFMessageGetHasRichText = OPFMessageGetHasRichText
                if email.get_OPFMessageGetHasRichText():
                    has_richtext = bool(
                        float(email.get_OPFMessageGetHasRichText().get_valueOf_()))
                    result['has_richtext'] = has_richtext
                    log.debug('has_richtext:[{}]'.format(has_richtext))
                    # assert(0)

                # def get_OPFMessageGetIsRead(self): return self.OPFMessageGetIsRead
                # def set_OPFMessageGetIsRead(self, OPFMessageGetIsRead): self.OPFMessageGetIsRead = OPFMessageGetIsRead
                if email.get_OPFMessageGetIsRead():
                    is_read = bool(
                        float(email.get_OPFMessageGetIsRead().get_valueOf_()))
                    result['is_read'] = is_read
                    log.debug('is_read:[{}]'.format(is_read))
                    # assert(0)

                # def get_OPFMessageGetOverrideEncoding(self): return self.OPFMessageGetOverrideEncoding
                # def set_OPFMessageGetOverrideEncoding(self, OPFMessageGetOverrideEncoding): self.OPFMessageGetOverrideEncoding = OPFMessageGetOverrideEncoding
                if email.get_OPFMessageGetOverrideEncoding():
                    override_encoding = float(
                        bool(email.get_OPFMessageGetOverrideEncoding().get_valueOf_()))
                    result['override_encoding'] = override_encoding
                    log.debug('override_encoding:[{}]'.format(
                        override_encoding))
                    # assert(0)

                # def get_OPFMessageGetPriority(self): return self.OPFMessageGetPriority
                # def set_OPFMessageGetPriority(self, OPFMessageGetPriority): self.OPFMessageGetPriority = OPFMessageGetPriority
                if email.get_OPFMessageGetPriority():
                    priority = email.get_OPFMessageGetPriority().get_valueOf_()
                    result['priority'] = priority
                    log.debug('priority:[{}]'.format(priority))
                    # assert(0)

                # def get_OPFMessageCopySource(self): return self.OPFMessageCopySource
                # def set_OPFMessageCopySource(self, OPFMessageCopySource): self.OPFMessageCopySource = OPFMessageCopySource
                if email.get_OPFMessageCopySource():
                    source = email.get_OPFMessageCopySource().get_valueOf_()
                    result['source'] = source
                    log.debug('source:[{}]'.format(source))
                    # Todo: need to check what is source, seems to be a email

                # def get_OPFMessageCopyGetFlagStatus(self): return self.OPFMessageCopyGetFlagStatus
                # def set_OPFMessageCopyGetFlagStatus(self, OPFMessageCopyGetFlagStatus): self.OPFMessageCopyGetFlagStatus = OPFMessageCopyGetFlagStatus
                if email.get_OPFMessageCopyGetFlagStatus():
                    flag_status = email.get_OPFMessageCopyGetFlagStatus().get_valueOf_()
                    result['flag_status'] = flag_status
                    log.debug('flag_status:[{}]'.format(flag_status))
                    # assert(0)

                # def get_OPFMessageGetWasSent(self): return self.OPFMessageGetWasSent
                # def set_OPFMessageGetWasSent(self, OPFMessageGetWasSent): self.OPFMessageGetWasSent = OPFMessageGetWasSent
                if email.get_OPFMessageGetWasSent():
                    was_sent = bool(
                        float(email.get_OPFMessageGetWasSent().get_valueOf_()))
                    result['was_sent'] = was_sent
                    log.debug('was_sent:[{}]'.format(was_sent))
                    # assert(0)

                # def get_OPFMessageIsCalendarMessage(self): return self.OPFMessageIsCalendarMessage
                # def set_OPFMessageIsCalendarMessage(self, OPFMessageIsCalendarMessage): self.OPFMessageIsCalendarMessage = OPFMessageIsCalendarMessage
                if email.get_OPFMessageIsCalendarMessage():
                    calendar_message = email.get_OPFMessageIsCalendarMessage().get_valueOf_()
                    result['calendar_message'] = calendar_message
                    log.debug('calendar_message:[{}]'.format(calendar_message))
                    # assert(0)

                # def get_OPFMessageIsMeeting(self): return self.OPFMessageIsMeeting
                # def set_OPFMessageIsMeeting(self, OPFMessageIsMeeting): self.OPFMessageIsMeeting = OPFMessageIsMeeting
                if email.get_OPFMessageIsMeeting():
                    is_meeting = bool(
                        float(email.get_OPFMessageIsMeeting().get_valueOf_()))
                    result['is_meeting'] = is_meeting
                    log.debug('is_meeting:[{}]'.format(is_meeting))
                    assert(0)

                # def get_OPFMessageIsOutgoing(self): return self.OPFMessageIsOutgoing
                # def set_OPFMessageIsOutgoing(self, OPFMessageIsOutgoing): self.OPFMessageIsOutgoing = OPFMessageIsOutgoing
                if email.get_OPFMessageIsOutgoing():
                    is_outgoing = bool(
                        float(email.get_OPFMessageIsOutgoing().get_valueOf_()))
                    result['is_outgoing'] = is_outgoing
                    log.debug('is_outgoing:[{}]'.format(is_outgoing))
                    # assert(0)

                # def get_OPFMessageIsOutgoingMeetingResponse(self): return self.OPFMessageIsOutgoingMeetingResponse
                # def set_OPFMessageIsOutgoingMeetingResponse(self, OPFMessageIsOutgoingMeetingResponse): self.OPFMessageIsOutgoingMeetingResponse = OPFMessageIsOutgoingMeetingResponse
                if email.get_OPFMessageIsOutgoingMeetingResponse():
                    is_outgoing_meeting_respoonse = bool(
                        float(email.get_OPFMessageIsOutgoingMeetingResponse().get_valueOf_()))
                    result['is_outgoing_meeting_respoonse'] = is_outgoing_meeting_respoonse
                    log.debug('is_outgoing_meeting_respoonse:[{}]'.format(
                        is_outgoing_meeting_respoonse))
                    # assert(0)

                ################################################################
                # address start

                # def get_OPFMessageCopyBCCAddresses(self): return self.OPFMessageCopyBCCAddresses
                # def set_OPFMessageCopyBCCAddresses(self, OPFMessageCopyBCCAddresses): self.OPFMessageCopyBCCAddresses = OPFMessageCopyBCCAddresses
                bcc_addresses = email.get_OPFMessageCopyBCCAddresses()
                if bcc_addresses:
                    result['bcc_addresses'] = parse_addresses(bcc_addresses)
                    log.debug('bcc_addresses: {}'.format(
                        result['bcc_addresses']))

                # def get_OPFMessageCopyReplyToAddresses(self): return self.OPFMessageCopyReplyToAddresses
                # def set_OPFMessageCopyReplyToAddresses(self, OPFMessageCopyReplyToAddresses): self.OPFMessageCopyReplyToAddresses = OPFMessageCopyReplyToAddresses
                replyto_addresses = email.get_OPFMessageCopyReplyToAddresses()
                if replyto_addresses:
                    result['replyto_addresses'] = parse_addresses(
                        replyto_addresses)
                    log.debug('replyto_addresses: {}'.format(
                        result['replyto_addresses']))

                # def get_OPFMessageCopySenderAddress(self): return self.OPFMessageCopySenderAddress
                # def set_OPFMessageCopySenderAddress(self, OPFMessageCopySenderAddress): self.OPFMessageCopySenderAddress = OPFMessageCopySenderAddress
                sender_address = email.get_OPFMessageCopySenderAddress()
                if sender_address:
                    result['sender_address'] = parse_addresses(
                        sender_address)
                    log.debug('sender_address: {}'.format(
                        result['sender_address']))
                    # assert(0)

                # def get_OPFMessageCopyToAddresses(self): return self.OPFMessageCopyToAddresses
                # def set_OPFMessageCopyToAddresses(self, OPFMessageCopyToAddresses): self.OPFMessageCopyToAddresses = OPFMessageCopyToAddresses
                to_addresses = email.get_OPFMessageCopyToAddresses()
                if to_addresses:
                    result['to_addresses'] = parse_addresses(
                        to_addresses)
                    log.debug('to_addresses: {}'.format(
                        result['to_addresses']))

                # def get_OPFMessageCopyFromAddresses(self): return self.OPFMessageCopyFromAddresses
                # def set_OPFMessageCopyFromAddresses(self, OPFMessageCopyFromAddresses): self.OPFMessageCopyFromAddresses = OPFMessageCopyFromAddresses
                from_addresses = email.get_OPFMessageCopyFromAddresses()
                if from_addresses:
                    result['from_addresses'] = parse_addresses(
                        from_addresses)
                    log.debug('from_addresses: {}'.format(
                        result['from_addresses']))

                # def get_OPFMessageCopyCCAddresses(self): return self.OPFMessageCopyCCAddresses
                # def set_OPFMessageCopyCCAddresses(self, OPFMessageCopyCCAddresses): self.OPFMessageCopyCCAddresses = OPFMessageCopyCCAddresses
                cc_addresses = email.get_OPFMessageCopyCCAddresses()
                if cc_addresses:
                    result['cc_addresses'] = parse_addresses(
                        cc_addresses)
                    log.debug('cc_addresses: {}'.format(
                        result['cc_addresses']))

                # address end
                ################################################################

                ########################################################
                # Category Start
                # def get_OPFMessageCopyPrimaryCategory(self): return self.OPFMessageCopyPrimaryCategory
                # def set_OPFMessageCopyPrimaryCategory(self, OPFMessageCopyPrimaryCategory): self.OPFMessageCopyPrimaryCategory = OPFMessageCopyPrimaryCategory
                primary_category = email.get_OPFMessageCopyPrimaryCategory()
                if primary_category:
                    background_color = primary_category.get_OPFCategoryCopyBackgroundColor().get_valueOf_()
                    category_name = primary_category.get_OPFCategoryCopyName().get_valueOf_()
                    result['primary_category'] = {}
                    result['primary_category']['background_color'] = background_color
                    result['primary_category']['category_name'] = category_name

                    log.debug(
                        'primary_category:[{}]/[{}]'.format(category_name, background_color))

                # def get_OPFMessageCopyCategoryList(self): return self.OPFMessageCopyCategoryList
                # def set_OPFMessageCopyCategoryList(self, OPFMessageCopyCategoryList): self.OPFMessageCopyCategoryList = OPFMessageCopyCategoryList
                category_list = email.get_OPFMessageCopyCategoryList()
                django_category_list = []
                if category_list:
                    for category in category_list.get_category():
                        background_color = category.get_OPFCategoryCopyBackgroundColor()
                        category_name = category.get_OPFCategoryCopyName()
                        django_category = {}
                        django_category['background_color'] = background_color
                        django_category['category_name'] = category_name
                        django_category_list.append(django_category)
                        log.debug('category_list:[{}], [{}]'.format(
                            background_color, category_name))
                result['category_list'] = django_category_list
                # Category End
                ########################################################

                #############################################
                # Meeting Start
                # def get_OPFMessageCopyMeetingData(self): return self.OPFMessageCopyMeetingData
                # def set_OPFMessageCopyMeetingData(self, OPFMessageCopyMeetingData): self.OPFMessageCopyMeetingData = OPFMessageCopyMeetingData
                if email.get_OPFMessageCopyMeetingData():
                    meeting_data = email.get_OPFMessageCopyMeetingData().get_valueOf_()
                    result['meeting_data'] = meeting_data
                    log.debug('meeting_data:[{}]'.format(meeting_data))
                    # Todo: need implement reference process future
                    # 2018-08-01 03:20:41 PM|WARNING|Skip not xml file: [Local/com.microsoft.__Messages/Sent Items/com.microsoft.__Attachments/637B248F-0DFA-46B9-B0C0-708DEEDE34DF@pset.suntec.net.ics]
                    # 2018-08-01 03:20:41
                    # PM|INFO|meeting_data:[Local/com.microsoft.__Messages/Sent
                    # Items/com.microsoft.__Attachments/637B248F-0DFA-46B9-B0C0-708DEEDE34DF@pset.suntec.net.ics]
                # Meeting End
                #############################################

                # def get_OPFMessageCopyAttachmentList(self): return self.OPFMessageCopyAttachmentList
                # def set_OPFMessageCopyAttachmentList(self, OPFMessageCopyAttachmentList): self.OPFMessageCopyAttachmentList = OPFMessageCopyAttachmentList
                attachments = email.get_OPFMessageCopyAttachmentList()
                result['attachments'] = []
                if attachments:
                    count = 0
                    for attachment in attachments.get_messageAttachment():
                        log.debug('Attchment [{}]: {}, {}, {}, {}, {}, {}'.format(
                            count,
                            attachment.get_OPFAttachmentContentExtension(),
                            float(attachment.get_OPFAttachmentContentFileSize()
                                  ) / 1024.,
                            attachment.get_OPFAttachmentContentFileSize(),
                            # attachment.get_OPFAttachmentContentID(),
                            attachment.get_OPFAttachmentContentType(),
                            attachment.get_OPFAttachmentName(),
                            attachment.get_OPFAttachmentURL(),
                        ))
                        attachment_django = {}
                        attachment_django['content_extension'] = attachment.get_OPFAttachmentContentExtension(
                        )

                        attachment_django['content_filesize'] = float(
                            attachment.get_OPFAttachmentContentFileSize())
                        # attachment.get_OPFAttachmentContentID(),
                        attachment_django['content_type'] = attachment.get_OPFAttachmentContentType(
                        )
                        attachment_django['content_name'] = attachment.get_OPFAttachmentName(
                        )
                        attachment_django['olm_item_url'] = attachment.get_OPFAttachmentURL(
                        )
                        count += 1
                        result['attachments'].append(attachment_django)

                # job used to add email to django site
                add_email.delay(result)
            return True
            # todo: need implement attachment process future


@shared_task
def add_email(email_result, full_check=False):
    olm_filename = email_result.get('olm_filename', '')
    olm_item_url = email_result.get('olm_item_url', '')
    message_id = email_result.get('message_id', '')

    django_email, created = Email.objects.get_or_create(
        olm_filename=olm_filename,
        olm_item_url=olm_item_url,
        message_id=message_id,
    )

    if (not created) and (not full_check):
        log.debug('Skip existed email object:[{}|{}|{}]'.format(
            olm_filename,
            olm_item_url,
            message_id,
        ))
        return django_email.id

    # 1 create email
    django_email.thread_topic = email_result.get('thread_topic', '')
    django_email.subject = email_result.get('subject', '')
    django_email.thread_index = email_result.get('thread_index', '')
    django_email.received_time = email_result.get('received_time', None)
    django_email.sent_time = parser.parse(email_result.get('sent_time', None))
    django_email.completed_datetime = email_result.get(
        'completed_datetime', None)
    django_email.due_datetime = email_result.get('due_datetime', None)
    django_email.start_datetime = email_result.get('start_datetime', None)
    django_email.mod_date = email_result.get('mod_date', None)
    django_email.reminder_datetime = email_result.get(
        'reminder_datetime', None)
    django_email.has_html = email_result.get('has_html', None)
    django_email.body = email_result.get('body', '')
    django_email.html_body = email_result.get('html_body', '')
    django_email.references = email_result.get('references', '')
    django_email.replyto = email_result.get('replyto', '')
    django_email.receive_representing_name = email_result.get(
        'receive_representing_name', '')
    django_email.calendar_accept_status = email_result.get(
        'calendar_accept_status', '')
    django_email.send_read_receipt = email_result.get('send_read_receipt', '')
    django_email.mentioned_me = email_result.get('mentioned_me', None)
    django_email.inference_classfication = email_result.get(
        'inference_classfication', '')
    django_email.has_richtext = email_result.get('has_richtext', None)
    django_email.is_read = email_result.get('is_read', None)
    django_email.override_encoding = email_result.get('override_encoding', '')
    django_email.priority = email_result.get('priority', '')
    django_email.source = email_result.get('source', '')
    django_email.flag_status = email_result.get('flag_status', '')
    django_email.was_sent = email_result.get('is_read', None)
    django_email.calendar_message = email_result.get('calendar_message', '')
    django_email.is_meeting = email_result.get('is_meeting', None)
    django_email.is_outgoing = email_result.get('is_outgoing', None)
    django_email.is_outgoing_meeting_respoonse = email_result.get(
        'is_outgoing_meeting_respoonse', None)

    django_email.save()

    # 2. after create email
    # 2.1 create addresses
    django_bcc_addresses = []
    for bcc_address_result in email_result.get('bcc_addresses', []):
        django_bcc_address, created = Address.objects.get_or_create(
            address=bcc_address_result.get('address', ''),
            name=bcc_address_result.get('name', ''),
            content_type=bcc_address_result.get('content_type', ''),
        )
        django_bcc_addresses.append(django_bcc_address)
    if django_bcc_addresses:
        django_email.bcc_addresses.add(*django_bcc_addresses)

    django_replyto_addresses = []
    for replyto_address_result in email_result.get('replyto_addresses', []):
        django_replyto_address, created = Address.objects.get_or_create(
            address=replyto_address_result.get('address', ''),
            name=replyto_address_result.get('name', ''),
            content_type=replyto_address_result.get('content_type', ''),
        )
        django_replyto_addresses.append(django_replyto_address)
    if django_replyto_addresses:
        django_email.replyto_addresses.add(*django_replyto_addresses)

    django_sender_addresses = []
    for sender_address_result in email_result.get('sender_addresses', []):
        django_sender_address, created = Address.objects.get_or_create(
            address=sender_address_result.get('address', ''),
            name=sender_address_result.get('name', ''),
            content_type=sender_address_result.get('content_type', ''),
        )
        django_sender_addresses.append(django_sender_address)
    if django_sender_addresses:
        django_email.django_sender_addresses.add(*django_sender_address)

    django_to_addresses = []
    for to_address_result in email_result.get('to_addresses', []):
        django_to_address, created = Address.objects.get_or_create(
            address=to_address_result.get('address', ''),
            name=to_address_result.get('name', ''),
            content_type=to_address_result.get('content_type', ''),
        )
        django_to_addresses.append(django_to_address)
    if django_to_addresses:
        django_email.to_addresses.add(*django_to_addresses)

    django_from_addresses = []
    for from_address_result in email_result.get('from_addresses', []):
        django_from_address, created = Address.objects.get_or_create(
            address=from_address_result.get('address', ''),
            name=from_address_result.get('name', ''),
            content_type=from_address_result.get('content_type', ''),
        )
        django_from_addresses.append(django_from_address)
    if django_from_addresses:
        django_email.from_addresses.add(*django_from_addresses)

    django_cc_addresses = []
    for cc_address_result in email_result.get('cc_addresses', []):
        django_cc_address, created = Address.objects.get_or_create(
            address=cc_address_result.get('address', ''),
            name=cc_address_result.get('name', ''),
            content_type=cc_address_result.get('content_type', ''),
        )
        django_cc_addresses.append(django_cc_address)
    if django_cc_addresses:
        django_email.cc_addresses.add(
            *django_cc_addresses)

    # 2.2 create category
    primary_category_result = email_result.get('primary_category', None)
    if primary_category_result:
        primary_category, created = Category.objects.get_or_create(
            name=primary_category_result.get('category_name', ''),
            color=primary_category_result.get(
                'background_color', ''),
        )
        django_email.primary_category = primary_category
        django_email.save()

    category_list_result = email_result.get('cc_addresses', [])
    if category_list_result:
        django_category_list = []
        for category_result in category_list_result:
            name = category_result.get('category_name', '')
            color = category_result.get(
                'background_color', '')
            if name:
                django_category_result, created = Category.objects.get_or_create(
                    name=name,
                    color=color,
                )
                django_category_list.append(django_category_result)
        django_email.category_list.add(*django_category_list)

    # 2.3 create meeting
    meeting_data = email_result.get('meeting_data', None)
    if meeting_data:

        django_meeting = export_fileobj_to_django(
            olm_filename, meeting_data, Meeting)
        django_email.meeting_data = django_meeting
        django_email.save()

    # 2.4 create attachment
    attachment_list = email_result.get('attachments', None)
    if attachment_list:
        for attachment in attachment_list:

            django_attachment, created = Attachment.objects.get_or_create(
                olm_filename=olm_filename,
                olm_item_url=attachment.get('olm_item_url', ''),
                email=django_email,
            )
            if not created:
                log.error('This attachment has been used')
                continue

            with zipfile.ZipFile(olm_filename, mode='r', allowZip64=True) as zf:
                with zf.open(attachment.get('olm_item_url', '')) as zip_data:
                    django_attachment.file_obj = File(zip_data)

                    django_attachment.content_extension = attachment.get(
                        'content_extension', '')
                    django_attachment.content_filesize = attachment.get(
                        'content_filesize', None)
                    django_attachment.content_type = attachment.get(
                        'content_type', '')
                    django_attachment.content_name = attachment.get(
                        'content_name', '')
                    # django_attachment.email = django_email
                    django_attachment.save()
