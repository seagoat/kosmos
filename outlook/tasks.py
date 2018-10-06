# Create your tasks here
from __future__ import absolute_import, unicode_literals

import os
import zipfile

from celery import shared_task
from celery.utils.log import get_task_logger
from dateutil import parser
from django.core.files import File

from .models import Address, Attachment, Email, KosmosError
from .xml_parser import emails

log = get_task_logger(__name__)


def parse_address(address):
    result = {}

    result['address'] = address.get_OPFContactEmailAddressAddress()
    result['name'] = address.get_OPFContactEmailAddressName()
    result['content_type'] = address.get_OPFContactEmailAddressType()

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
        log.debug(olm_item_url)
        parse_contacts.delay(olm_filename, olm_item_url)
        return True

    elif dirs[-1] == 'Calendar.xml':
        log.debug(olm_item_url)
        parse_calendar.delay(olm_filename, olm_item_url)
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
        # if ret == False:
        #     msg = 'parse_email failed to parse:[{}]'.format(olm_item_url)
        #     log.error(msg)
        #     return False
        # else:
        #     return True
        return True

    else:
        msg = 'Unsupported xml file: [{}]'.format(olm_item_url)
        log.error(msg)
        return False


@shared_task
def record_error(olm_filename, olm_item_url):
    kosmos_error, created = KosmosError.objects.get_or_create(
        olm_filename=olm_filename,
        olm_item_url=olm_item_url,
    )

    if not created:
        return kosmos_error.id

    with zipfile.ZipFile(olm_filename, mode='r', allowZip64=True) as zf:
        with zf.open(olm_item_url) as xml_item:
            kosmos_error.file_obj = File(xml_item)
            kosmos_error.save()

    return kosmos_error.id


@shared_task
def parse_calendar(olm_filename, olm_item_url):
    # todo
    pass


@shared_task
def parse_contacts(olm_filename, olm_item_url):
    # todo
    pass


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
                    log.info('message_id:[{}]'.format(message_id))
                    # assert(0)

                # def get_OPFMessageCopyThreadTopic(self): return self.OPFMessageCopyThreadTopic
                # def set_OPFMessageCopyThreadTopic(self, OPFMessageCopyThreadTopic): self.OPFMessageCopyThreadTopic = OPFMessageCopyThreadTopic
                if email.get_OPFMessageCopyThreadTopic():
                    thread_topic = email.get_OPFMessageCopyThreadTopic().get_valueOf_()
                    result['thread_topic'] = thread_topic
                    log.debug('thread_topic:[{}]'.format(thread_topic))

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
                    received_time = parser.parse(
                        email.get_OPFMessageCopyReceivedTime().get_valueOf_())
                    result['received_time'] = received_time
                    log.debug('received_time:[{}]'.format(received_time))

                # def get_OPFMessageCopySentTime(self): return self.OPFMessageCopySentTime
                # def set_OPFMessageCopySentTime(self, OPFMessageCopySentTime): self.OPFMessageCopySentTime = OPFMessageCopySentTime
                if email.get_OPFMessageCopySentTime():
                    sent_time = parser.parse(
                        email.get_OPFMessageCopySentTime().get_valueOf_())
                    result['sent_time'] = sent_time
                    log.debug('sent_time:[{}]'.format(sent_time))

                # def get_OPFMessageCopyCompletedDateTime(self): return self.OPFMessageCopyCompletedDateTime
                # def set_OPFMessageCopyCompletedDateTime(self, OPFMessageCopyCompletedDateTime): self.OPFMessageCopyCompletedDateTime = OPFMessageCopyCompletedDateTime
                if email.get_OPFMessageCopyCompletedDateTime():
                    completed_datetime = parser.parse(
                        email.get_OPFMessageCopyCompletedDateTime().get_valueOf_())
                    result['completed_datetime'] = completed_datetime
                    log.debug('completed_datetime:[{}]'.format(
                        completed_datetime))

                # def get_OPFMessageCopyDueDateTime(self): return self.OPFMessageCopyDueDateTime
                # def set_OPFMessageCopyDueDateTime(self, OPFMessageCopyDueDateTime): self.OPFMessageCopyDueDateTime = OPFMessageCopyDueDateTime
                if email.get_OPFMessageCopyDueDateTime():
                    due_datetime = parser.parse(
                        email.get_OPFMessageCopyDueDateTime().get_valueOf_())
                    result['due_datetime'] = due_datetime
                    log.debug('due_datetime:[{}]'.format(due_datetime))

                # def get_OPFMessageCopyStartDateTime(self): return self.OPFMessageCopyStartDateTime
                # def set_OPFMessageCopyStartDateTime(self, OPFMessageCopyStartDateTime): self.OPFMessageCopyStartDateTime = OPFMessageCopyStartDateTime
                if email.get_OPFMessageCopyStartDateTime():
                    start_datetime = parser.parse(
                        email.get_OPFMessageCopyStartDateTime().get_valueOf_())
                    result['start_datetime'] = start_datetime
                    log.debug('start_datetime:[{}]'.format(start_datetime))

                # def get_OPFMessageCopyModDate(self): return self.OPFMessageCopyModDate
                # def set_OPFMessageCopyModDate(self, OPFMessageCopyModDate): self.OPFMessageCopyModDate = OPFMessageCopyModDate
                if email.get_OPFMessageCopyModDate():
                    mod_date = parser.parse(
                        email.get_OPFMessageCopyModDate().get_valueOf_())
                    result['mod_date'] = mod_date
                    log.debug('mode_date:[{}]'.format(mod_date))

                # def get_OPFMessageCopyReminderDateTime(self): return self.OPFMessageCopyReminderDateTime
                # def set_OPFMessageCopyReminderDateTime(self, OPFMessageCopyReminderDateTime): self.OPFMessageCopyReminderDateTime = OPFMessageCopyReminderDateTime
                if email.get_OPFMessageCopyReminderDateTime():
                    reminder_datetime = parser.parse(
                        email.get_OPFMessageCopyReminderDateTime().get_valueOf_())
                    result['reminder_datetime'] = reminder_datetime
                    log.debug('reminder_datetime:[{}]'.format(
                        reminder_datetime))
                    assert(0)

                # def get_OPFMessageGetHasHTML(self): return self.OPFMessageGetHasHTML
                # def set_OPFMessageGetHasHTML(self, OPFMessageGetHasHTML): self.OPFMessageGetHasHTML = OPFMessageGetHasHTML
                if email.get_OPFMessageGetHasHTML():
                    has_html = email.get_OPFMessageGetHasHTML().get_valueOf_()
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

                # def get_OPFMessageCopyPrimaryCategory(self): return self.OPFMessageCopyPrimaryCategory
                # def set_OPFMessageCopyPrimaryCategory(self, OPFMessageCopyPrimaryCategory): self.OPFMessageCopyPrimaryCategory = OPFMessageCopyPrimaryCategory
                primary_category = email.get_OPFMessageCopyPrimaryCategory()
                if primary_category:
                    background_color = primary_category.get_OPFCategoryCopyBackgroundColor().get_valueOf_()
                    category_name = primary_category.get_OPFCategoryCopyName().get_valueOf_()
                    result['primary_category_background_color'] = background_color
                    result['primary_category_category_name'] = category_name

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

                # def get_OPFMessageCopyBCCAddresses(self): return self.OPFMessageCopyBCCAddresses
                # def set_OPFMessageCopyBCCAddresses(self, OPFMessageCopyBCCAddresses): self.OPFMessageCopyBCCAddresses = OPFMessageCopyBCCAddresses
                bcc_addresses = email.get_OPFMessageCopyBCCAddresses()
                result['bcc_addresses'] = parse_addresses(bcc_addresses)
                log.debug('bcc_addresses: {}'.format(result['bcc_addresses']))

                # def get_OPFMessageCopyReplyToAddresses(self): return self.OPFMessageCopyReplyToAddresses
                # def set_OPFMessageCopyReplyToAddresses(self, OPFMessageCopyReplyToAddresses): self.OPFMessageCopyReplyToAddresses = OPFMessageCopyReplyToAddresses
                replyto_addresses = email.get_OPFMessageCopyReplyToAddresses()
                result['replyto_addresses'] = parse_addresses(
                    replyto_addresses)
                log.debug('replyto_addresses: {}'.format(
                    result['replyto_addresses']))

                # def get_OPFMessageCopySenderAddress(self): return self.OPFMessageCopySenderAddress
                # def set_OPFMessageCopySenderAddress(self, OPFMessageCopySenderAddress): self.OPFMessageCopySenderAddress = OPFMessageCopySenderAddress
                sender_addresses = email.get_OPFMessageCopySenderAddress()
                result['sender_addresses'] = parse_addresses(
                    sender_addresses)
                log.debug('sender_addresses: {}'.format(
                    result['sender_addresses']))
                # assert(0)

                # def get_OPFMessageCopyToAddresses(self): return self.OPFMessageCopyToAddresses
                # def set_OPFMessageCopyToAddresses(self, OPFMessageCopyToAddresses): self.OPFMessageCopyToAddresses = OPFMessageCopyToAddresses
                to_addresses = email.get_OPFMessageCopyToAddresses()
                result['to_addresses'] = parse_addresses(
                    to_addresses)
                log.debug('to_addresses: {}'.format(
                    result['to_addresses']))

                # def get_OPFMessageCopyFromAddresses(self): return self.OPFMessageCopyFromAddresses
                # def set_OPFMessageCopyFromAddresses(self, OPFMessageCopyFromAddresses): self.OPFMessageCopyFromAddresses = OPFMessageCopyFromAddresses
                from_addresses = email.get_OPFMessageCopyFromAddresses()
                result['from_addresses'] = parse_addresses(
                    from_addresses)
                log.debug('from_addresses: {}'.format(
                    result['from_addresses']))

                # def get_OPFMessageCopyCCAddresses(self): return self.OPFMessageCopyCCAddresses
                # def set_OPFMessageCopyCCAddresses(self, OPFMessageCopyCCAddresses): self.OPFMessageCopyCCAddresses = OPFMessageCopyCCAddresses
                cc_addresses = email.get_OPFMessageCopyCCAddresses()
                result['cc_addresses'] = parse_addresses(
                    cc_addresses)
                log.debug('cc_addresses: {}'.format(
                    result['cc_addresses']))

                # def get_OPFMessageCopyReceivedRepresentingName(self): return self.OPFMessageCopyReceivedRepresentingName
                # def set_OPFMessageCopyReceivedRepresentingName(self, OPFMessageCopyReceivedRepresentingName): self.OPFMessageCopyReceivedRepresentingName = OPFMessageCopyReceivedRepresentingName
                if email.get_OPFMessageCopyReceivedRepresentingName():
                    receive_representing_name = parser.parse(
                        email.get_OPFMessageCopyReceivedRepresentingName().get_valueOf_())
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
                    mentioned_me = email.get_OPFMessageGetMentionedMe().get_valueOf_()
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
                    has_richtext = email.get_OPFMessageGetHasRichText().get_valueOf_()
                    result['has_richtext'] = has_richtext
                    log.debug('has_richtext:[{}]'.format(has_richtext))
                    # assert(0)

                # def get_OPFMessageGetIsRead(self): return self.OPFMessageGetIsRead
                # def set_OPFMessageGetIsRead(self, OPFMessageGetIsRead): self.OPFMessageGetIsRead = OPFMessageGetIsRead
                if email.get_OPFMessageGetIsRead():
                    is_read = email.get_OPFMessageGetIsRead().get_valueOf_()
                    result['is_read'] = is_read
                    log.debug('is_read:[{}]'.format(is_read))
                    # assert(0)

                # def get_OPFMessageGetOverrideEncoding(self): return self.OPFMessageGetOverrideEncoding
                # def set_OPFMessageGetOverrideEncoding(self, OPFMessageGetOverrideEncoding): self.OPFMessageGetOverrideEncoding = OPFMessageGetOverrideEncoding
                if email.get_OPFMessageGetOverrideEncoding():
                    override_encoding = email.get_OPFMessageGetOverrideEncoding().get_valueOf_()
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

                # def get_OPFMessageCopySubject(self): return self.OPFMessageCopySubject
                # def set_OPFMessageCopySubject(self, OPFMessageCopySubject): self.OPFMessageCopySubject = OPFMessageCopySubject
                if email.get_OPFMessageCopySubject():
                    subject = email.get_OPFMessageCopySubject().get_valueOf_()
                    result['subject'] = subject
                    log.debug('subject:[{}]'.format(subject))
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
                    was_sent = email.get_OPFMessageGetWasSent().get_valueOf_()
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
                    is_meeting = email.get_OPFMessageIsMeeting().get_valueOf_()
                    result['is_meeting'] = is_meeting
                    log.debug('is_meeting:[{}]'.format(is_meeting))
                    assert(0)

                # def get_OPFMessageIsOutgoing(self): return self.OPFMessageIsOutgoing
                # def set_OPFMessageIsOutgoing(self, OPFMessageIsOutgoing): self.OPFMessageIsOutgoing = OPFMessageIsOutgoing
                if email.get_OPFMessageIsOutgoing():
                    is_outgoing = email.get_OPFMessageIsOutgoing().get_valueOf_()
                    result['is_outgoing'] = is_outgoing
                    log.debug('is_outgoing:[{}]'.format(is_outgoing))
                    # assert(0)

                # def get_OPFMessageIsOutgoingMeetingResponse(self): return self.OPFMessageIsOutgoingMeetingResponse
                # def set_OPFMessageIsOutgoingMeetingResponse(self, OPFMessageIsOutgoingMeetingResponse): self.OPFMessageIsOutgoingMeetingResponse = OPFMessageIsOutgoingMeetingResponse
                if email.get_OPFMessageIsOutgoingMeetingResponse():
                    is_outgoing_meeting_respoonse = email.get_OPFMessageIsOutgoingMeetingResponse().get_valueOf_()
                    result['is_outgoing_meeting_respoonse'] = is_outgoing_meeting_respoonse
                    log.debug('is_outgoing_meeting_respoonse:[{}]'.format(
                        is_outgoing_meeting_respoonse))
                    # assert(0)

                # def get_OPFMessageCopyAttachmentList(self): return self.OPFMessageCopyAttachmentList
                # def set_OPFMessageCopyAttachmentList(self, OPFMessageCopyAttachmentList): self.OPFMessageCopyAttachmentList = OPFMessageCopyAttachmentList
                attachments = email.get_OPFMessageCopyAttachmentList()
                result['attachments'] = []
                if attachments:
                    count = 0
                    for attachment in attachments.get_messageAttachment():
                        log.info('Attchment [{}]: {}, {}, {}, {}, {}, {}'.format(
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

                        attachment_django['content_filesize'] = attachment.get_OPFAttachmentContentFileSize(
                        ),
                        # attachment.get_OPFAttachmentContentID(),
                        attachment_django['content_type'] = attachment.get_OPFAttachmentContentType(
                        )
                        attachment_django['content_name'] = attachment.get_OPFAttachmentName(
                        )
                        attachment_django['content_url'] = attachment.get_OPFAttachmentURL(
                        )
                        count += 1
                        result['attachments'].append(attachment_django)
                add_email.delay(result)
            return True
            # todo: need implement attachment process future


@shared_task
def add_email(email_result, full_check=False):

    django_email, created = Email.objects.get_or_create(
        olm_filename=email_result['olm_filename'],
        olm_item_url=email_result['olm_item_url'],
        message_id=email_result['message_id'],
    )

    if (not created) and (not full_check):
        log.debug('Skip existed email object:[{}|{}|{}]'.format(
            email_result['olm_filename'],
            email_result['olm_item_url'],
            email_result['message_id'],
        ))
        return django_email.id

    # 1. before create email
    # 1.1 create addresses

    # 1.2 create category

    # 1.3 create meeting

    # 2 create email
    django_email.subject = email_result.get('subject', None)
    django_email.save()

    # 3 after create mail
    # 3.0 create attachment
