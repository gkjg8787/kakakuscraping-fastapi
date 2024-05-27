from datetime import datetime

from proc.server_log.extract_server_log import CreateExtractServerLogCommand


class TestCreateExtractServerLogCommand:

    def test_get_closest_start_date_range_2days_not_same(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = datetime(2024, 5, 4)
        near_start = CreateExtractServerLogCommand().get_closest_start_date(
            datelist=datelist, start=start, end=end
        )
        assert near_start == start

    def test_get_closest_start_date_range_2days_same(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = datetime(2024, 5, 3)
        near_start = CreateExtractServerLogCommand().get_closest_start_date(
            datelist=datelist, start=start, end=end
        )
        assert near_start == start

    def test_get_closest_start_date_start_is_none(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = None
        end = datetime(2024, 5, 3)
        near_start = CreateExtractServerLogCommand().get_closest_start_date(
            datelist=datelist, start=start, end=end
        )
        assert near_start == start

    def test_get_closest_start_date_end_is_none(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = None
        near_start = CreateExtractServerLogCommand().get_closest_start_date(
            datelist=datelist, start=start, end=end
        )
        assert near_start == start

    def test_get_closest_start_date_start_exceeds_lower_limit(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 1)
        end = datetime(2024, 5, 4)
        near_start = CreateExtractServerLogCommand().get_closest_start_date(
            datelist=datelist, start=start, end=end
        )
        assert near_start == datetime(2024, 5, 2)

    def test_get_closest_start_date_start_exceeds_upper_limit(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 21)
        end = datetime(2024, 5, 23)
        near_start = CreateExtractServerLogCommand().get_closest_start_date(
            datelist=datelist, start=start, end=end
        )
        assert near_start == None

    def test_get_closest_day_following_end_date_range_2days_not_same(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = datetime(2024, 5, 4)
        near_end = CreateExtractServerLogCommand().get_closest_day_following_end_date(
            datelist=datelist, start=start, end=end
        )
        assert near_end == datetime(2024, 5, 20)

    def test_get_closest_day_following_end_date_range_2days_same(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = datetime(2024, 5, 3)
        near_end = CreateExtractServerLogCommand().get_closest_day_following_end_date(
            datelist=datelist, start=start, end=end
        )
        assert near_end == datetime(2024, 5, 4)

    def test_get_closest_day_following_end_date_start_is_none(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = None
        end = datetime(2024, 5, 3)
        near_end = CreateExtractServerLogCommand().get_closest_day_following_end_date(
            datelist=datelist, start=start, end=end
        )
        assert near_end == datetime(2024, 5, 4)

    def test_get_closest_day_following_end_date_end_is_none(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = None
        near_end = CreateExtractServerLogCommand().get_closest_day_following_end_date(
            datelist=datelist, start=start, end=end
        )
        assert near_end == None

    def test_get_closest_day_following_end_date_end_exceeds_upper_limit(self):
        datelist = [
            datetime(2024, 5, 2),
            datetime(2024, 5, 3),
            datetime(2024, 5, 4),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = datetime(2024, 5, 21)
        near_end = CreateExtractServerLogCommand().get_closest_day_following_end_date(
            datelist=datelist, start=start, end=end
        )
        assert near_end == datetime(2024, 5, 20)

    def test_get_closest_day_following_end_date_end_exceeds_lower_limit(self):
        datelist = [
            datetime(2024, 5, 5),
            datetime(2024, 5, 6),
            datetime(2024, 5, 7),
            datetime(2024, 5, 20),
        ]
        start = datetime(2024, 5, 3)
        end = datetime(2024, 5, 4)
        near_end = CreateExtractServerLogCommand().get_closest_day_following_end_date(
            datelist=datelist, start=start, end=end
        )
        assert near_end == None
