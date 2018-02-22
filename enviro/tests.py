from django.test import TestCase
from enviro.models import MeasureFile
from enviro.views import *
from django.utils import timezone
from django.core.exceptions import *
import os

f = os.path.isfile('/Users/Tobias/Documents/DjangoEnviroment/EngineeringApp/TestDataUpload/beispiel.csv')


class MeasureFileTest(TestCase):
    def setDB(self, title="test", upload_date=timezone.now(), start_year=1950, end_year=1990, location="Ostereistedt",
              measure_file="f"):
        return MeasureFile.objects.create(title=title, upload_date=upload_date, start_year=start_year,
                                          end_year=end_year, location=location, measure_file=f)

    def test_exception(self):
        m = self.setDB()
        self.assertTrue(isinstance(m, MeasureFile))
        self.assertRaises(ValidationError, m=self.setDB(start_year="1272127"))
        self.assertRaises(ValidationError, m=self.setDB(end_year="1272127"))
        self.assertRaises(ValidationError, m=self.setDB(end_year="-1"))
        self.assertRaises(ValidationError, m=self.setDB(start_year="-1"))
        self.assertRaises(FieldError, m=self.setDB(title="testtesttesttesttesttesttest"))
        self.assertRaises(FieldError, m=self.setDB(location="testtesttesttesttesttesttest"))
        self.assertRaises(ValidationError, m=self.setDB(measure_file="beispiel.png"))

        try:
            x = False
            m = self.setDB(start_year="test")
        except ValueError:
            x = True

        self.assertTrue(x)

        try:
            x = False
            m = self.setDB(end_year="test")
        except ValueError:
            x = True

        self.assertTrue(x)