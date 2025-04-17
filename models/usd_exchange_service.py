import logging
import requests
from datetime import datetime, timedelta
from odoo import models, api

_logger = logging.getLogger(__name__)

class USDExchangeService(models.Model):
    _name = 'usd.exchange.service'
    _description = 'Servicio de actualización de tipo de cambio USD desde Banxico'

    @api.model
    def update_usd_exchange_rate(self):
        _logger.info("🚀 Ejecutando update_usd_exchange_rate desde usd.exchange.service...")

        url_base = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos/"
        token = self.env['ir.config_parameter'].sudo().get_param('usd_exchange.banxico_token')
        if not token:
            _logger.error("No se ha configurado el token de Banxico en parámetros del sistema.")
            return

        # Obtener fecha anterior (día hábil)
        fecha = datetime.now()
        if fecha.weekday() == 0:
            fecha -= timedelta(days=3)
        else:
            fecha -= timedelta(days=1)
        fecha_str = fecha.strftime('%Y-%m-%d')

        url = f"{url_base}{fecha_str}/{fecha_str}/?token={token}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            tipo_cambio_str = data['bmx']['series'][0]['datos'][0]['dato']
            tipo_cambio = float(tipo_cambio_str)
            tasa = 1 / tipo_cambio

            usd_currency = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
            if not usd_currency:
                _logger.error("No se encontró la moneda USD en el sistema.")
                return

            # Eliminar tasa anterior si existe
            existing_rate = self.env['res.currency.rate'].sudo().search([
                ('currency_id', '=', usd_currency.id),
                ('name', '=', fecha_str)
            ])
            if existing_rate:
                existing_rate.unlink()

            self.env['res.currency.rate'].sudo().create({
                'currency_id': usd_currency.id,
                'rate': tasa,
                'name': fecha_str,
            })

            _logger.info(f"✅ Tipo de cambio USD actualizado exitosamente: 1/{tipo_cambio} = {tasa}")
        except Exception as e:
            _logger.exception("❌ Error al actualizar tipo de cambio desde Banxico: %s", str(e))
