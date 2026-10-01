"""Desde el proyecto: python -m unittest discover -s tests -p 'test_factura_montos.py'"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from factura_montos import (
    METADATA, _leer_ot_metadata, actualizar_carpeta, es_factura, extraer_importes,
    numero_factura, numero_clp, resumen,
)


class MontosTests(unittest.TestCase):
    def test_prefijo_estricto(self):
        correctos = ['F N°587.pdf', 'f nº 361-362.pdf', 'F N°1778.jpg', 'F N°06.png']
        incorrectos = ['DETALLE F N°587.pdf', 'detalle F N°587.jpg', 'FACTURA 587.pdf', 'F N 587.pdf',
                      ' F N°587.pdf', 'F N°587.txt', 'OT.txt']
        for nombre in correctos:
            with self.subTest(nombre=nombre): self.assertTrue(es_factura(nombre))
        for nombre in incorrectos:
            with self.subTest(nombre=nombre): self.assertFalse(es_factura(nombre))
        self.assertEqual(numero_factura('F N°0587.pdf'), '0587')

    def test_importes_clp(self):
        self.assertEqual(numero_clp('123.529'), 123529)
        self.assertEqual(numero_clp('23,471'), 23471)
        self.assertEqual(numero_clp('147000'), 147000)
        self.assertIsNone(numero_clp('12,34'))

    def test_pdf_sii_texto_sintetico(self):
        texto = ('FACTURA ELECTRONICA N°587\n'
                 'Descripción Cantidad Precio Valor\nCOLACIONES 21 5882,33 123.529\n'
                 'MONTO NETO $ 123.529\nI.V.A. 19% $ 23.471\n'
                 'IMPUESTO ADICIONAL $ 0\nTOTAL $ 147.000')
        self.assertEqual(extraer_importes(texto)[0], {'neto': 123529, 'iva': 23471, 'total': 147000})
        self.assertIsNone(extraer_importes('imagen escaneada sin importes')[0])
        self.assertIsNone(extraer_importes('NETO 100\nIVA 19\nTOTAL 500')[0])

    def test_foto_pendiente_y_metadata_preservada(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'F N°587.jpg').write_bytes(b'foto de prueba')
            Path(d, 'DETALLE F N°587.jpg').write_bytes(b'detalle de prueba')
            filas = resumen(d)
            self.assertEqual(len(filas['documentos']), 1)
            self.assertEqual(filas['pendientes'], 1)
            self.assertEqual(filas['sumas']['total'], 0)
            self.assertTrue(Path(d, METADATA).exists())
            self.assertEqual(len(actualizar_carpeta(d, forzar=True)), 1)

    def test_metadata_manual_no_se_pisa(self):
        from factura_montos import _leer_metadata, _guardar_metadata, _huella
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d, 'F N°587.jpg')
            ruta.write_bytes(b'foto')
            actualizar_carpeta(d)
            data = _leer_metadata(d)
            data['documentos'][ruta.name].update(estado='manual', montos={'neto': 100, 'iva': 19, 'total': 119})
            _guardar_metadata(d, data)
            self.assertEqual(resumen(d)['sumas']['total'], 119)
            self.assertEqual(actualizar_carpeta(d, forzar=True)[0]['estado'], 'manual')
            ruta.write_bytes(b'foto cambiada')
            self.assertEqual(actualizar_carpeta(d)[0]['estado'], 'manual')

    def test_ot_metadata_prefiere_archivo_oculto(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, 'OT.txt').write_text('OT-ANTIGUA', encoding='utf-8')
            self.assertEqual(_leer_ot_metadata(d), 'OT-ANTIGUA')

            Path(d, '.OT.txt').write_text('OT-NUEVA', encoding='utf-8')
            self.assertEqual(_leer_ot_metadata(d), 'OT-NUEVA')

    def test_pdf_real_generado_si_hay_pymupdf(self):
        try:
            import fitz
        except ImportError:
            self.skipTest('PyMuPDF no instalado en el entorno de prueba')
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d,'F N°999.pdf')
            doc = fitz.open()
            pagina = doc.new_page()
            pagina.insert_text((80, 80), 'MONTO NETO $ 123.529\nI.V.A. 19% $ 23.471\nTOTAL $ 147.000')
            doc.save(ruta)
            doc.close()
            self.assertEqual(resumen(d)['sumas']['total'], 147000)


if __name__ == '__main__':
    unittest.main()
