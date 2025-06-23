# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime

from kajson import kajson


class TestEncoderRegistration:
    """Test that encoders are properly registered."""

    def test_date_encoder_registered(self) -> None:
        """Test that date encoder is registered with UniversalJSONEncoder."""
        from kajson.json_encoder import UniversalJSONEncoder

        assert UniversalJSONEncoder.is_encoder_registered(datetime.date)
        encoder_func = UniversalJSONEncoder.get_registered_encoder(datetime.date)
        assert encoder_func is kajson.json_encode_date

    def test_datetime_encoder_registered(self) -> None:
        """Test that datetime encoder is registered with UniversalJSONEncoder."""
        from kajson.json_encoder import UniversalJSONEncoder

        assert UniversalJSONEncoder.is_encoder_registered(datetime.datetime)
        encoder_func = UniversalJSONEncoder.get_registered_encoder(datetime.datetime)
        assert encoder_func is kajson.json_encode_datetime

    def test_time_encoder_registered(self) -> None:
        """Test that time encoder is registered with UniversalJSONEncoder."""
        from kajson.json_encoder import UniversalJSONEncoder

        assert UniversalJSONEncoder.is_encoder_registered(datetime.time)
        encoder_func = UniversalJSONEncoder.get_registered_encoder(datetime.time)
        assert encoder_func is kajson.json_encode_time

    def test_timedelta_encoder_registered(self) -> None:
        """Test that timedelta encoder is registered with UniversalJSONEncoder."""
        from kajson.json_encoder import UniversalJSONEncoder

        assert UniversalJSONEncoder.is_encoder_registered(datetime.timedelta)
        encoder_func = UniversalJSONEncoder.get_registered_encoder(datetime.timedelta)
        assert encoder_func is kajson.json_encode_timedelta

    def test_date_decoder_registered(self) -> None:
        """Test that date decoder is registered with UniversalJSONDecoder."""
        from kajson.json_decoder import UniversalJSONDecoder

        assert UniversalJSONDecoder.is_decoder_registered(datetime.date)
        decoder_func = UniversalJSONDecoder.get_registered_decoder(datetime.date)
        assert decoder_func is kajson.json_decode_date

    def test_datetime_decoder_registered(self) -> None:
        """Test that datetime decoder is registered with UniversalJSONDecoder."""
        from kajson.json_decoder import UniversalJSONDecoder

        assert UniversalJSONDecoder.is_decoder_registered(datetime.datetime)
        decoder_func = UniversalJSONDecoder.get_registered_decoder(datetime.datetime)
        assert decoder_func is kajson.json_decode_datetime

    def test_time_decoder_registered(self) -> None:
        """Test that time decoder is registered with UniversalJSONDecoder."""
        from kajson.json_decoder import UniversalJSONDecoder

        assert UniversalJSONDecoder.is_decoder_registered(datetime.time)
        decoder_func = UniversalJSONDecoder.get_registered_decoder(datetime.time)
        assert decoder_func is kajson.json_decode_time
