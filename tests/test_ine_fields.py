import unittest

from app.parsing.ine_fields import parse_front


class IneFieldsParsingTests(unittest.TestCase):
    def test_parses_name_address_and_electoral_data(self):
        result = parse_front([
            "NOMBRE", "ARELLANO", "HERNANDEZ", "GIOVANNI EDUARDO",
            "DOMICILIO", "C COSTA DE LOS VINOS 23", "COL ASTILLEROS 91800",
            "VERACRUZ VER", "AÑO DE REGISTRO 2019 00", "SECCION 4228",
            "VIGENCIA 2019-2029",
        ])
        self.assertEqual(result["nombre_completo"]["valor"], "ARELLANO HERNANDEZ GIOVANNI EDUARDO")
        self.assertEqual(result["domicilio"]["numero_exterior"], "23")
        self.assertEqual(result["domicilio"]["codigo_postal"], "91800")
        self.assertEqual(result["datos_electorales"]["seccion"], "4228")
        self.assertEqual(result["datos_electorales"]["emision"], "00")

    def test_keeps_unprinted_location_fields_empty(self):
        result = parse_front(["NOMBRE", "LOPEZ", "GARCIA", "ANA"])
        self.assertIsNone(result["datos_electorales"]["municipio"])
        self.assertIsNone(result["datos_electorales"]["localidad"])

    def test_accepts_labels_and_values_on_same_line(self):
        result = parse_front([
            "NOMBRE ARELLANO", "HERNANDEZ", "GIOVANNIE EDUARDO",
            "DOMICILIO C COSTA 23", "COL ASTILLEROS 91800", "VERACRUZ VER",
        ])
        self.assertEqual(result["nombre_completo"]["apellido_paterno"], "ARELLANO")
        self.assertEqual(result["domicilio"]["calle"], "COSTA")
        self.assertEqual(result["domicilio"]["colonia"], "ASTILLEROS")

    def test_accepts_electoral_values_on_following_lines(self):
        result = parse_front([
            "AÑODEREGISTR", "ATD", "201900", "SECCION", "VIGENCIA",
            "FECHADENACIMIENTO", "2019-2029", "03/10/2001", "4228",
        ])
        self.assertEqual(result["datos_electorales"]["anio_registro"], "2019")
        self.assertEqual(result["datos_electorales"]["emision"], "00")
        self.assertEqual(result["datos_electorales"]["seccion"], "4228")


if __name__ == "__main__":
    unittest.main()
