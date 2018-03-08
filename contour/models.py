from django.utils import timezone
from .validators import validate_file_extension
from django.db import models
from user.models import User
from django.core.exceptions import ValidationError
import random
import string

# Thanks to: https://stackoverflow.com/questions/34239877/django-save-user-
# uploads-in-seperate-folders
def measurement_directory_path(instance, filename):
    """
    Creates the path where to upload a measurement file.

    The path is:
    MEDIA_ROOT/<username>/measurement/<pk>/<filename>_<random_hash>

    Parameters
    ----------
    instance : MeasureFileModel,
        The MeasureFileModel object that has the measurement file which needs
        a directory.
    filename : String,
        Name of the measurement file, e.g. "data_points.csv".

    Returns
    -------
    summed_fields : ndarray, dtype=Bool
        Boolean array of shape like array with True if element was used in summation.
    last_summed : float
        Element that was added last to the sum.
    """
    random_hash = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=10))
    return '{0}/measurement/{1}'.format(
        instance.primary_user.username,
        filename + '_' + random_hash)


class MeasureFileModel(models.Model):
    """
    Model for a file containing measurement data.

    A MeasureFileModel object holds a measurement file. It is associated to a
    user (owner) and can be shared with other users.
    """
    primary_user = models.ForeignKey(User, null=True, related_name="primary")
    secondary_user = models.ManyToManyField(User,
                                            related_name="secondary",
                                            max_length=50)
    title = models.CharField(default="MeasureFile", max_length=50)
    upload_date = models.DateTimeField(default=timezone.now)
    measure_file = models.FileField(
        upload_to=measurement_directory_path,
        validators=[validate_file_extension])
    path_of_statics = models.CharField(default=None, max_length=240, null=True)

    @staticmethod
    def url_str():
        return "measure_file_model"


class ProbabilisticModel(models.Model):
    """
    Model for a multivariate distribution, e.g. a sea state description.

    A ProbabilisticModel object is associated to a user (owner) and can be
    shared with other users. It has a name and can be connected to
    measurement data.
    If a probabilistic model is defined, in addition X DistributionModel objects
    are needed to define the distributions.
    """

    primary_user = models.ForeignKey(User, null=True,
                                     related_name="variables_primary")
    secondary_user = models.ManyToManyField(User,
                                            related_name="variables_secondary")
    upload_date = models.DateTimeField(default=timezone.now)
    collection_name = models.CharField(default='VariablesCollection',
                                       max_length=50)
    path_of_statics = models.CharField(default=None, max_length=240, null=True)
    measure_file_model = models.ForeignKey(MeasureFileModel,
                                           on_delete=models.CASCADE,
                                           null=True)

    @staticmethod
    def url_str():
        return "probabilistic_model"


class DistributionModel(models.Model):
    """
    Model for the distribution of a single random variable.

    For example the random variable significant wave height, can be defined
    with this model. Its name would be 'significant wave height', its
    symbol 'Hs' and its distribution 'Weibull'. In addition one would need 3
    ParameterModel objects, which define the distributions parameters (scale,
    shape, location).
    """
    DISTRIBUTIONS = (('Normal', 'Normal Distribution'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-Normal'),
                     ('KernelDensity', 'Kernel Density'))
    name = models.CharField(default="peak period", max_length=50)
    symbol = models.CharField(default="Tp", max_length=5)
    distribution = models.CharField(choices=DISTRIBUTIONS, max_length=15)
    probabilistic_model = models.ForeignKey(ProbabilisticModel,
                                            on_delete=models.CASCADE)

    @staticmethod
    def url_str():
        return "distribution"


class ParameterModel(models.Model):
    """
    Model for one parameter of a distribution, e.g. scale.

    The parameter model can either be a constant value, e.g. x0 = 1.5 or
    it can be a function, which describes the parameter's depedency on
    another variable. The two available funtions have 3 parameters each, which
    are represented by x0, x1 and x2.
    """
    FUNCTIONS = ((None, 'None'), ('f1', 'power function'),
                 ('f2', 'exponential'))
    function = models.CharField(choices=FUNCTIONS, max_length=6)
    x0 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10,
                             null=True)
    x1 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10,
                             null=True)
    x2 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10,
                             null=True)
    dependency = models.CharField(default='!', max_length=10)
    # The name attribute can be 'scale', 'shape', or 'location' (see views.py)
    name = models.CharField(default='empty', max_length=10)
    distribution = models.ForeignKey(DistributionModel,
                                     on_delete=models.CASCADE)

    def clean(self):
        """
        Validates if the parameter of a distribution has valid values.

        For example a Normal distribution's scale parameter (sigma) must
        be > 0. If this is not the case, a ValidationError is raised.
        """
        # If the parameters are given as constant values
        if self.function == 'None':
            pass
        if self.distribution.distribution == 'Normal':
            if self.name == 'scale' and self.x0 <= 0:
                raise ValidationError(
                    "The Normal distribution's scale parameter, sigma, "
                    "must be > 0.")
        elif self.distribution.distribution == 'Weibull':
            if self.name == 'scale' and self.x0 <= 0:
                raise ValidationError(
                    "The Weibull distribution's scale parameter, lambda, "
                    "must be > 0.")
            elif self.name == 'shape' and self.x0 <= 0:
                raise ValidationError(
                    "The Weibull distribution's shape parameter, k, "
                    "must be > 0.")
        elif self.distribution.distribution == 'Lognormal_2':
            if self.name == 'shape' and self.x0 <= 0:
                raise ValidationError(
                    "The Log-normal's distribution's shape parameter, sigma, "
                    "must be > 0.")

    def __str__(self):
        return "ParameterModel object with: function=%r, x0=%r, x1=%r, x2=%r," \
               " dependency=%r, name=%r" % \
               (self.function, self.x0, self.x1, self.x2,
                self.dependency, self.name)


class EnvironmentalContour(models.Model):
    """
    Model for an environmental contour.

    The model contains the the settings, which were used to create the contour
    and the primary key to the probabilistic model on which it is based on.
    Additional options, which are a dictionary, have their own model
    (AdditionalContourOption) and are connected via the primary key to an
    EnvironmentalContour instance. The contour's path (the EEDCs) are also
    connected via two own models (Contourpath and ExtremeEnvDesignCondition).
    """
    primary_user = models.ForeignKey(User, null=True,
                                     related_name="contours_primary")
    secondary_user = models.ManyToManyField(User,
                                            related_name="contours_secondary")
    fitting_method = models.CharField(default=None, max_length=240)
    contour_method = models.CharField(default=None, max_length=240)
    return_period = models.DecimalField(decimal_places=5, max_digits=10)
    state_duration = models.DecimalField(decimal_places=5, max_digits=10)
    path_of_statics = models.CharField(default=None, max_length=240, null=True)
    probabilistic_model = models.ForeignKey(ProbabilisticModel,
                                     on_delete=models.CASCADE)

    @staticmethod
    def url_str():
        return "environmental_contour"

class AdditionalContourOption(models.Model):
    """
    Additional options describing how an environmental contour was created.

    Since different environmental contour methods are available some options
    are only applicable to one method. Consequently, AdditionalContourOption
    can be used as a dictionary to specify additional options.

    Idea how this model works is based on this stackoverflow post: https://stack
    overflow.com/questions/402217/how-to-store-a-dictionary-on-a-django-model
    """
    # Key can for example be "Number of points on the contour"
    option_key = models.CharField(default=None, max_length=240, null=True)
    # Then value can for example be "50"
    option_value = models.CharField(default=None, max_length=240, null=True)
    environmental_contour = models.ForeignKey(EnvironmentalContour,
                                              on_delete=models.CASCADE)


class ContourPath(models.Model):
    """
    Model for the path of an environmental contour.

    One or multiple ContourPath instances can be associated to an
    EnvironmentalContour instance.

    The points of the path have their own model (ExtremeEnvDesignCondition)
    and are connected via the ContourPath primary key.
    """
    environmental_contour = models.ForeignKey(EnvironmentalContour,
                                              on_delete=models.CASCADE)


class ExtremeEnvDesignCondition(models.Model):
    """
    Model for a single extreme environmental design conditions.


    Multiple ExtremeEnvDesignCondition instances make up a ContourPath instance.

    For each dimension an EEDCScalar instance is needed and connected via the
    primary key to an ExtremeEnvDesignCondition instance.
    """
    contour_path = models.ForeignKey(ContourPath, on_delete=models.CASCADE)


class EEDCScalar(models.Model):
    """
    Model for the value of one dimension of an extreme env. design condition.

    Multiple EEDCScalar instances make up an ExtremEnvDesignCondition instance.
    """
    x = models.DecimalField(decimal_places=5, max_digits=10, null=True)
    EEDC = models.ForeignKey(ExtremeEnvDesignCondition,
                                     on_delete=models.CASCADE)