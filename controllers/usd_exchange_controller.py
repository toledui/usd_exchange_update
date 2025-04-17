from odoo import http
from odoo.http import request, Response
from datetime import datetime, timedelta
import requests
import logging

_logger = logging.getLogger(__name__)

class USDExchangeController(http.Controller):

    @http.route('/usd/exchange/update', type='http', auth='user')
    def update_usd_exchange(self, **kw):
        try:
            # Restar un día hábil (simple)
            fecha = datetime.now()

            fecha_str = fecha.strftime('%Y-%m-%d')

            api_key = request.env['ir.config_parameter'].sudo().get_param('banxico_api_key')
            if not api_key:
                return Response("API Key no configurada", status=500)

            serie = "SF60653"
            url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{fecha_str}/{fecha_str}/?token={api_key}"
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Extraer tipo de cambio
            tipo_cambio_str = data['bmx']['series'][0]['datos'][0]['dato']
            tipo_cambio = float(tipo_cambio_str.replace(",", ""))  # Banxico a veces lo da con coma

            # Buscar moneda USD
            moneda_usd = request.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
            if not moneda_usd:
                return Response("No se encontró la moneda USD", status=404)

            # Guardar tipo de cambio (rate es: 1 / tipo_cambio)
            rate_value = round(1 / tipo_cambio, 6)

            request.env['res.currency.rate'].sudo().create({
                'currency_id': moneda_usd.id,
                'rate': rate_value,
                'name': fecha.date()
            })

            return Response(f"Tipo de cambio actualizado: {tipo_cambio} MXN/USD (guardado como rate={rate_value})", status=200)

        except Exception as e:
            _logger.exception("Error al actualizar el tipo de cambio USD")
            return Response(f"Error: {str(e)}", status=500)
