import sqlite3

from app.data.city_data_source import CityDataSource


class TestFindByName:
    def test_match_ignores_case_accents_and_surrounding_spaces(
        self, connection: sqlite3.Connection
    ) -> None:
        city = CityDataSource(connection).find_by_name("  campos do jordao ")

        assert city is not None
        assert city.model_dump() == {
            "id": 3,
            "name": "Campos do Jordão",
            "state": "SP",
            "country": "Brasil",
            "latitude": -22.7394,
            "longitude": -45.5914,
        }

    def test_city_abroad_carries_its_country(
        self, connection: sqlite3.Connection
    ) -> None:
        city = CityDataSource(connection).find_by_name("lisboa")

        assert city is not None
        assert city.country == "Portugal"

    def test_city_outside_the_catalog(self, connection: sqlite3.Connection) -> None:
        assert CityDataSource(connection).find_by_name("Gramado") is None


class TestCreateCity:
    def test_new_city_is_stored_and_returned_with_its_generated_id(
        self, connection: sqlite3.Connection
    ) -> None:
        city = CityDataSource(connection).create_city(
            "Curitiba", "PR", "Brasil", -25.4296, -49.2713
        )

        row = connection.execute(
            "SELECT id, name, state, country, latitude, longitude"
            " FROM cities WHERE name = 'Curitiba'"
        ).fetchone()
        assert (
            city.model_dump()
            == dict(row)
            == {
                "id": city.id,
                "name": "Curitiba",
                "state": "PR",
                "country": "Brasil",
                "latitude": -25.4296,
                "longitude": -49.2713,
            }
        )


class TestListCities:
    def test_cities_in_alphabetical_order(self, connection: sqlite3.Connection) -> None:
        names = [city.name for city in CityDataSource(connection).list_cities()]

        assert names == sorted(names)
        assert len(names) == 11
