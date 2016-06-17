# -*- coding: utf-8 -*-

import json
import logging
import pprint
import werkzeug
import base64

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class EpaybgController(http.Controller):
    _return_url = '/shop/confirmation'
    # _return_url = '/payment/epaybg/return'

    @http.route([
        '/payment/epaybg/return',
    ], type='http', auth='none', csrf=False)
    def epaybg_return(self, **post):
        _logger.info('Beginning epaybg_return form_feedback with post data %s', pprint.pformat(post))  # debug

        return_url = post.pop('return_url', '')
        request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'epaybg', context=request.context)

        # if post.get('authResult') not in ['CANCELLED']:
        #     request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'epaybg', context=request.context)
        # return_url = post.pop('return_url', '')
        # if not return_url:
        #     custom = json.loads(post.pop('merchantReturnData', '{}'))
        #     return_url = custom.pop('return_url', '/')
        return werkzeug.utils.redirect(return_url)

    @http.route([
        '/payment/epaybg/notification',
    ], type='http', auth='none', methods=['POST'], csrf=False)
    def epaybg_notification(self, **post):
        _logger.info('Beginning epaybg_notification form_feedback with post data %s', pprint.pformat(post))  # debug

        encoded, checksum = post.get('encoded'), post.get('checksum')

        if not encoded or not checksum:
            return ''

        epay_decoded_result = self.epay_decoded_result(encoded)
        tx_id = int(epay_decoded_result['INVOICE'])

        tx = request.registry['payment.transaction'].browse(request.cr, SUPERUSER_ID, tx_id, context=request.context)

        if not tx:
            # XXX if not recognise this invoice
            status = 'NO'
        elif epay_decoded_result['STATUS'] == 'PAID':
            # XXX if OK for this invoice
            status = 'OK'
        else:
            # XXX if error for this invoice
            status = 'ERR'

        info_data = "INVOICE=%s:STATUS=%s\n" % (tx_id, status)

        _logger.critical(info_data)

        return info_data

    def _epaybg_generate_merchant_decoded(self, encoded):
        return base64.b64decode(encoded)

    def epay_decoded_result(self, encoded):
        result = self._epaybg_generate_merchant_decoded(encoded)
        words = result.split(":")
        dict1 = {}
        if len(words) > 0:
            for word in words:
                w = word.split("=")
                if len(w) > 0:
                    dict1[w[0]] = w[1]
        return dict1
