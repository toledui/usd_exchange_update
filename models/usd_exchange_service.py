import logging
import requests
from datetime import datetime, timedelta

from odoo import models, api

_logger = logging.getLogger(__name__)

class USDExchangeService(models.Model):
    _name = 'usd.exchange.service'
    _description = 'Servicio de actualización de tipo de cambio desde Banxico'

    @api.model
    def update_usd_exchange_rate(self):
        token = self.env['ir.config_parameter'].sudo().get_param('usd_exchange.banxico_token')
        if not token:
            _logger.error("No se ha configurado el token de Banxico.")
            return

        fecha = datetime.now()
        if fecha.weekday() == 0:
            fecha -= timedelta(days=3)
        else:
            fecha -= timedelta(days=1)

        fecha_str = fecha.strftime('%Y-%m-%d')
        url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos/{fecha_str}/{fecha_str}/?token={token}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            tipo_cambio = float(data['bmx']['series'][0]['datos'][0]['dato'])
            tasa = round(1 / tipo_cambio, 6)

            usd_currency = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
            if not usd_currency:
                _logger.error("No se encontró la moneda USD en el sistema.")
                return

            self.env['res.currency.rate'].sudo().create({
                'currency_id': usd_currency.id,
                'rate': tasa,
                'name': fecha.strftime('%Y-%m-%d'),
            })

            _logger.info(f"Tipo de cambio USD actualizado correctamente: {tipo_cambio} (tasa: {tasa})")

        except Exception as e:
            _logger.exception("Error al obtener o guardar tipo de cambio USD desde Banxico: %s", str(e))
