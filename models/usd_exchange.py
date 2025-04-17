import logging
import requests
from datetime import datetime, timedelta
from odoo import models, api
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class BanxicoExchangeRate(models.Model):
    _inherit = 'res.currency'

    @api.model
    def update_usd_exchange_rate(self):
        _logger.info("🕒 Ejecutando cron update_usd_exchange_rate()")
        url_base = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos/"
        token = self.env['ir.config_parameter'].sudo().get_param('usd_exchange.banxico_token')
        if not token:
            _logger.error("No se ha configurado el token de Banxico en parámetros del sistema.")
            return

        # Obtener fecha anterior (día hábil)
        fecha = datetime.now()
        fecha_str = fecha.strftime('%Y-%m-%d')

        url = f"{url_base}{fecha_str}/{fecha_str}/?token={token}"

        try:
            response = requests.get(url)
            if response.status_code != 200:
                _logger.error(f"Error al obtener datos de Banxico: {response.status_code}")
                return

            data = response.json()
            serie = data['bmx']['series'][0]['datos']
            if not serie:
                _logger.warning("No se encontraron datos para la fecha indicada.")
                return

            tipo_cambio_str = serie[0]['dato'].replace(',', '')
            tipo_cambio = float(tipo_cambio_str)
            tasa = round(1 / tipo_cambio, 6)

            # Buscar moneda USD
            usd_currency = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
            if not usd_currency:
                _logger.error("No se encontró la moneda USD en el sistema.")
                return

            # Crear nuevo registro de tipo de cambio
            self.env['res.currency.rate'].sudo().create({
                'currency_id': usd_currency.id,
                'rate': tasa,
                'name': fecha.strftime('%Y-%m-%d'),
            })

            _logger.info(f"Tipo de cambio USD actualizado: 1/{tipo_cambio} = {tasa}")
        except Exception as e:
            _logger.exception("Error al actualizar tipo de cambio desde Banxico: %s", str(e))
