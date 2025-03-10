"""Visualization of US census data on unemployment and participation.

Submission for Assignment 10 for Stat 198: Interactive Data Science and
Visualization demonstrating 6 variables from the US Census ACS Microdata sample.

Author: A Samuel Pottinger
License: BSD-3-Clause
"""
import itertools
import math

import sketchingpy

import data_model

WIDTH = 1100
HEIGHT = 900

LEFT_PAD = 10
RIGHT_PAD = 10
TOP_PAD = 40
BOTTOM_PAD = 10
GUTTER_PAD = 20

TOP_AXIS_HEIGHT = 14
BOTTOM_AXIS_HEIGHT = 14
BOTTOM_GRAPH_HEIGHT = 70

MAIN_Y_END = HEIGHT - sum([
    BOTTOM_PAD,
    BOTTOM_AXIS_HEIGHT,
    BOTTOM_GRAPH_HEIGHT,
    GUTTER_PAD
])
GENDER_PARTICIPATION_WIDTH = 300
INCOME_WIDTH = 200

START_X_GENDER_PARTICIPATION = LEFT_PAD
END_X_GENDER_PARTICIPATION = sum([
    START_X_GENDER_PARTICIPATION,
    GENDER_PARTICIPATION_WIDTH
])
START_Y_GENDER_PARTICIPATION = TOP_PAD + TOP_AXIS_HEIGHT
END_Y_GENDER_PARTICIPATION = MAIN_Y_END

START_X_UNEMPLOYMENT = END_X_GENDER_PARTICIPATION + GUTTER_PAD
START_Y_UNEMPLOYMENT = TOP_PAD + TOP_AXIS_HEIGHT
END_X_UNEMPLOYMENT = WIDTH - RIGHT_PAD - INCOME_WIDTH
END_Y_UNEMPLOYMENT = MAIN_Y_END

START_X_RACE_ETHNICITY = START_X_UNEMPLOYMENT
START_Y_RACE_ETHNICITY = MAIN_Y_END + GUTTER_PAD + BOTTOM_AXIS_HEIGHT
END_X_RACE_ETHNICITY = END_X_UNEMPLOYMENT
END_Y_RACE_ETHNICITY = HEIGHT - BOTTOM_PAD

START_X_INCOME = END_X_UNEMPLOYMENT + GUTTER_PAD
START_Y_INCOME = START_Y_UNEMPLOYMENT
END_X_INCOME = WIDTH - RIGHT_PAD
END_Y_INCOME = MAIN_Y_END

DARK_TEXT_COLOR = '#333333'
LIGHT_TEXT_COLOR = '#666666'
FEMALE_COLOR = '#1f78b4'
MALE_COLOR = '#33a02c'
OVERLAY_COLOR = '#FFFFFF'
OCCUPATION_AXIS_COLOR = '#E0E0E0'
GAP_COLOR = '#505050'

IS_ONLINE = False

FONT = 'PublicSans-Regular' if IS_ONLINE else 'PublicSans-Regular.otf'

TITLE = 'An Economy that Leaves Some Out'
PARTICIPATION_TITLE = '% of Workers in Occupation'
INCOME_TITLE = 'Median Income (Hr Equiv USD)'

DATA_LOC = 'data.csv'


class OccupationScale:
    """Scale which converts from docc03 occupation to vertical position."""

    def __init__(self, dataset):
        """Create a new vertical scale for occupation groups (docc03).

        Args:
            dataset: data_model.Dataset to use in constructing this scale.
        """
        self._occupations = sorted(dataset.get_docc03_vals())
        self._height = END_Y_UNEMPLOYMENT - START_Y_UNEMPLOYMENT

    def get_position(self, occupation):
        """Get the vertical position for an occupation.

        Args:
            occupation: String occuation name matching docc03.

        Returns:
            float: Vertical position which is expected to be within
                START_Y_UNEMPLOYMENT and END_Y_UNEMPLOYMENT.
        """
        index = self._occupations.index(occupation)
        index_offset = index + 0.5
        percent = index_offset / len(self._occupations)
        return self._height * percent


class UnemploymentScale:
    """Scale which converts from unemp unemployment to horizontal position."""

    def __init__(self, dataset):
        """Create a new unemployment scale.

        Args:
            dataset: The data_model.Dataset use in constructing this
                unemployment scale.
        """
        self._width = END_X_UNEMPLOYMENT - START_X_UNEMPLOYMENT

        def get_max_gender_unemployment(query):
            query.set_female(True)
            female_unemployment = dataset.get_unemp(query)

            query.set_female(False)
            male_unemployment = dataset.get_unemp(query)
            return max([female_unemployment, male_unemployment])

        def get_unemployment_for_occupation(occupation):
            query = data_model.Query()
            query.set_docc03(occupation)
            return get_max_gender_unemployment(query)

        def get_unemployment_for_race_ethnicity(group):
            query = data_model.Query()
            query.set_wbhaom(group)
            return get_max_gender_unemployment(query)

        occupations = dataset.get_docc03_vals()
        occupation_unemployments = map(
            get_unemployment_for_occupation,
            occupations
        )

        groups = dataset.get_wbhaom_vals()
        group_unemployments = map(
            get_unemployment_for_race_ethnicity,
            groups
        )

        unemployments = itertools.chain(
            occupation_unemployments,
            group_unemployments
        )

        self._max_unemployment = math.ceil(max(unemployments))

    def get_position(self, unemployment):
        """Get the horizontal position for an unemployment level.

        Args:
            unemployment: A unemp value (0 - 100) from data_model to convert.

        Returns:
            float: Horizontal pixel position within START_X_UNEMPLOYMENT and
                END_X_UNEMPLOYMENT.
        """
        percent = unemployment / self._max_unemployment
        return percent * self._width

    def get_max_unemployment(self):
        """Get the maximum unemployment (unemp) level expected.

        Returns:
            float: The expected maximum unemployment level.
        """
        return self._max_unemployment


class MainPresenter:
    """Main coordinating presenter which manages other presenters.

    Central presenter which ensures that presenters which operate the sub-
    graphics operate correctly, acting as a facade to the rest of the graphic.
    """

    def __init__(self, sketch, dataset):
        """Create a new main presenter, creating subpresenter in the process.

        Args:
            sketch: The sketchingpy.Sketch2D to use in drawing this
                graphic and its sub-graphics.
            dataset: The data_model.Dataset to use in drawing this graphic and
                its sub-graphics.
        """
        self._sketch = sketch
        self._dataset = dataset

        horiz_scale = UnemploymentScale(dataset)
        vert_scale = OccupationScale(dataset)
        self._unemployment_presenter = UnemploymentByGenderPresenter(
            sketch,
            dataset,
            horiz_scale,
            vert_scale
        )
        self._participation_presenter = ParticipationRateByGenderPresenter(
            sketch,
            dataset,
            vert_scale
        )
        self._race_ethnicity_presenter = RaceEthnicityUnemploymentPresenter(
            sketch,
            dataset,
            horiz_scale
        )
        self._income_presenter = GenderIncomePresenter(
            sketch,
            dataset,
            vert_scale
        )

    def draw(self):
        """Draw this graphic and its subgraphics. Includes title."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._draw_title()
        self._unemployment_presenter.draw()
        self._participation_presenter.draw()
        self._race_ethnicity_presenter.draw()
        self._income_presenter.draw()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_title(self):
        """Draw the main title at the top of the graphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(0, TOP_PAD)
        x = (END_X_UNEMPLOYMENT + START_X_UNEMPLOYMENT) / 2

        self._sketch.clear_stroke()
        self._sketch.set_fill(DARK_TEXT_COLOR)

        self._sketch.set_text_font(FONT, 25)
        self._sketch.set_text_align('center', 'bottom')
        self._sketch.draw_text(x, 0, TITLE)

        self._sketch.pop_style()
        self._sketch.pop_transform()


class ParticipationRateByGenderPresenter:
    """Presenter for the left-side graphic which shows participation.

    Presenter which displays a right side graphic which both identifies
    individual occupations and draws the gender participation rate
    (share of 100%) for that occuaption.
    """

    def __init__(self, sketch, dataset, vert_scale):
        """Create a new participation rate visualization.

        Args:
            sketch: The sketch to use to draw this subgraphic.
            dataset: The data_model.Dataset to draw in this subgraphic.
            vert_scale: The shared axis / scale for occupation.
        """
        self._sketch = sketch
        self._dataset = dataset
        self._vert_scale = vert_scale
        self._width = END_X_GENDER_PARTICIPATION - START_X_GENDER_PARTICIPATION

    def draw(self):
        """Draw this subgraphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._draw_axis()
        self._draw_body()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_axis(self):
        """Draw the axis for this subgraphic.

        Draw the axis indicating which side corresponds to which gender for the
        participating by gender and occuation left-side graphic.
        """
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(
            START_X_GENDER_PARTICIPATION,
            START_Y_GENDER_PARTICIPATION
        )

        self._sketch.set_text_font(FONT, 12)
        self._sketch.clear_stroke()

        self._sketch.set_text_align('left', 'bottom')
        self._sketch.set_fill(FEMALE_COLOR)
        self._sketch.draw_text(0, 0, 'Female')

        self._sketch.set_text_align('center', 'bottom')
        self._sketch.set_fill(DARK_TEXT_COLOR)
        self._sketch.draw_text(self._width / 2, 0, PARTICIPATION_TITLE)

        self._sketch.set_text_align('right', 'bottom')
        self._sketch.set_fill(MALE_COLOR)
        self._sketch.draw_text(self._width, 0, 'Male')

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_body(self):
        """Draw the actual occuaptions and their participation rates."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(
            START_X_GENDER_PARTICIPATION,
            START_Y_GENDER_PARTICIPATION
        )

        occupations = dataset.get_docc03_vals()
        for occupation in occupations:
            self._draw_occupation(occupation)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_occupation(self, occupation):
        """Draw an individual occupation and its participation rate.

        Args:
            occupation: The occupation to draw. This name should match the value
                found in docc03.
        """
        self._sketch.push_transform()
        self._sketch.push_style()

        y = self._vert_scale.get_position(occupation)
        self._sketch.translate(0, y)

        query = data_model.Query()
        query.set_docc03(occupation)

        query.set_female(True)
        num_female = self._dataset.get_size(query)

        query.set_female(False)
        num_male = self._dataset.get_size(query)

        total_count = num_male + num_female
        percent_female = num_female / total_count
        percent_male = num_male / total_count

        self._sketch.clear_stroke()
        self._sketch.set_rect_mode('corner')

        self._sketch.set_text_font(FONT, 12)
        self._sketch.set_fill(LIGHT_TEXT_COLOR)
        self._sketch.set_text_align('right', 'bottom')
        occupation_label = occupation.replace(' occupations', '')
        self._sketch.draw_text(self._width, -1, occupation_label)

        width_female = self._width * percent_female - 1
        width_male = self._width * percent_male - 1

        self._sketch.set_fill(FEMALE_COLOR)
        self._sketch.draw_rect(0, 0, width_female, 12)

        self._sketch.set_fill(MALE_COLOR)
        self._sketch.draw_rect(self._width - width_male, 0, width_male, 12)

        self._sketch.set_text_font(FONT, 10)
        self._sketch.set_fill(OVERLAY_COLOR)

        self._sketch.set_text_align('left', 'center')
        female_percent_label = '%.0f %%' % (percent_female * 100)
        self._sketch.draw_text(1, 6, female_percent_label)

        self._sketch.set_text_align('right', 'center')
        male_percent_label = '%.0f %%' % (percent_male * 100)
        self._sketch.draw_text(self._width - 1, 6, male_percent_label)

        self._sketch.pop_style()
        self._sketch.pop_transform()


class UnemploymentByGenderPresenter:
    """Draw the central unemployment by gender dot plot.

    Graphic which is central to the full visualization that shows dot plots
    which depict unemployment with two dots in different colors representing the
    census genders. This contains the horizontal axis but not the vertical which
    comes from the left-side subgraphic.
    """

    def __init__(self, sketch, dataset, horiz_scale, vert_scale):
        """Create a new unemployment gender dot plot.

        Args:
            sketch: The sketchingpy.Sketch2D in which to draw this central
                graphic.
            dataset: The data_model.Dataset to draw in this central figure.
        """
        self._sketch = sketch
        self._dataset = dataset
        self._horiz_scale = horiz_scale
        self._vert_scale = vert_scale
        self._width = END_X_UNEMPLOYMENT - START_X_UNEMPLOYMENT
        self._height = END_Y_UNEMPLOYMENT - START_Y_UNEMPLOYMENT

    def draw(self):
        """Draw this subgraphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._draw_axis()
        self._draw_body()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_axis(self):
        """Draw the unemployment horizontal axis."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(START_X_UNEMPLOYMENT, START_Y_UNEMPLOYMENT)

        self._draw_top_axis()
        self._draw_bottom_axis()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_top_axis(self):
        """Draw the subgraphic title (unemployment rate)"""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.clear_stroke()
        self._sketch.set_fill(DARK_TEXT_COLOR)
        self._sketch.set_text_align('center', 'bottom')
        self._sketch.set_text_font(FONT, 12)
        self._sketch.draw_text(self._width / 2, 0, 'Unemployment Rate')

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_bottom_axis(self):
        """Draw the individual percent labels at the bottom of the graphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(0, self._height)

        self._sketch.clear_stroke()
        self._sketch.set_fill(DARK_TEXT_COLOR)
        self._sketch.set_text_align('center', 'top')
        self._sketch.set_text_font(FONT, 12)

        max_unemployment = self._horiz_scale.get_max_unemployment()
        percents = range(0, max_unemployment + 1)
        for percent in percents:
            x = self._horiz_scale.get_position(percent)
            self._sketch.draw_text(x, 0, '%d%%' % percent)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_body(self):
        """Draw the central body of this graphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(START_X_UNEMPLOYMENT, START_Y_UNEMPLOYMENT)

        occupations = dataset.get_docc03_vals()
        for occupation in occupations:
            self._draw_occupation(occupation)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_occupation(self, occupation):
        """Draw an individual occupation in this graphic.

        Args:
            occupation: The name of the occupation to draw as appears in docc03.
        """
        self._sketch.push_transform()
        self._sketch.push_style()

        y = self._vert_scale.get_position(occupation)
        self._sketch.translate(0, y)

        self._sketch.clear_fill()

        self._sketch.set_stroke(OCCUPATION_AXIS_COLOR)
        self._sketch.draw_line(0, 0, self._width, 0)

        query = data_model.Query()
        query.set_docc03(occupation)

        query.set_female(True)
        female_unemployment = self._dataset.get_unemp(query)

        query.set_female(False)
        male_unemployment = self._dataset.get_unemp(query)

        female_x = self._horiz_scale.get_position(female_unemployment)
        male_x = self._horiz_scale.get_position(male_unemployment)

        self._sketch.set_stroke(GAP_COLOR)
        self._sketch.draw_line(female_x, 0, male_x, 0)

        self._sketch.set_ellipse_mode('radius')
        self._sketch.set_text_align('center', 'center')
        self._sketch.set_text_font(FONT, 12)

        self._sketch.set_fill(FEMALE_COLOR)
        self._sketch.set_stroke(GAP_COLOR)
        self._sketch.draw_ellipse(female_x, 0, 10, 10)

        self._sketch.set_fill(OVERLAY_COLOR)
        self._sketch.clear_stroke()
        self._sketch.draw_text(female_x, 0, '%.0f' % female_unemployment)

        self._sketch.set_fill(MALE_COLOR)
        self._sketch.set_stroke(GAP_COLOR)
        self._sketch.draw_ellipse(male_x, 0, 10, 10)

        self._sketch.set_fill(OVERLAY_COLOR)
        self._sketch.clear_stroke()
        self._sketch.draw_text(male_x, 0, '%.0f' % male_unemployment)

        self._sketch.pop_style()
        self._sketch.pop_transform()


class RaceEthnicityUnemploymentPresenter:
    """Presenter for the bottom-side race / ethnicity unemployment graphic.

    Presenter for the bottom-side race / ethnicity unemployment dot plot which
    depicts unemployment rates by male / female (census definition) per
    occupation.
    """

    def __init__(self, sketch, dataset, horiz_scale):
        """Create a new right-side race / ethnicity plot.

        Args:
            sketch: The sketchingpy.Sketch2D instance in which to draw.
            dataset: The data_model.Dataset instance from which to draw.
            horiz_scale: Scale to use in calculating position corresponding to
                an unemployment rate.
        """
        self._sketch = sketch
        self._dataset = dataset
        self._horiz_scale = horiz_scale
        self._groups = sorted(dataset.get_wbhaom_vals())
        self._width = END_X_RACE_ETHNICITY - START_X_RACE_ETHNICITY
        self._height = END_Y_RACE_ETHNICITY - START_Y_RACE_ETHNICITY

    def draw(self):
        """Draw the right-side race / ethnicity plot."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(START_X_RACE_ETHNICITY, START_Y_RACE_ETHNICITY)

        for group in self._groups:
            self._draw_group(group)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_group(self, group):
        """Draw a single group.

        Draw a single group (wbhaom race / ethnicity) with male and female
        unemployment wihtin that group.

        Args:
            group: The group to draw where this string label matches a wbhaom
                group name.
        """
        self._sketch.push_transform()
        self._sketch.push_style()

        query = data_model.Query()
        query.set_wbhaom(group)

        query.set_female(True)
        female_unemployment = self._dataset.get_unemp(query)
        female_x = self._horiz_scale.get_position(female_unemployment)

        query.set_female(False)
        male_unemployment = self._dataset.get_unemp(query)
        male_x = self._horiz_scale.get_position(male_unemployment)

        y = self._get_group_position(group)
        self._sketch.translate(0, y)
        self._sketch.set_text_font(FONT, 12)
        self._sketch.set_text_align('right', 'center')
        self._sketch.set_ellipse_mode('radius')

        self._sketch.clear_fill()

        self._sketch.set_stroke(OCCUPATION_AXIS_COLOR)
        self._sketch.draw_line(0, 0, self._width, 0)

        self._sketch.set_stroke(GAP_COLOR)
        self._sketch.draw_line(male_x, 0, female_x, 0)

        self._sketch.clear_stroke()

        self._sketch.set_fill(LIGHT_TEXT_COLOR)
        self._sketch.draw_text(-1 * GUTTER_PAD, 0, group)

        self._sketch.set_fill(FEMALE_COLOR)
        self._sketch.draw_ellipse(female_x, 0, 5, 5)

        self._sketch.set_fill(MALE_COLOR)
        self._sketch.draw_ellipse(male_x, 0, 5, 5)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _get_group_position(self, group):
        """Get the position of a race or ethnicity.

        Args:
            group: The name of the group matching wbhaom from the Census.

        Returns:
            float: Vertical position in pixels.
        """
        index = self._groups.index(group)
        index_offset = index + 0.5
        percent = index_offset / len(self._groups)
        return self._height * percent


class GenderIncomePresenter:
    """Presenter which draws the right-side display of median hourly income.

    Presenter which draws the right-side display of median hourly income by
    gender where each occupation gets a grouped bar (two bars with one for
    each gender).
    """

    def __init__(self, sketch, dataset, vert_scale):
        """Create a right-side new gender income display.

        Args:
            sketch: The sketchingpy.Sketch2D instance in which to draw.
            dataset: The data_model.Dataset from which to draw.
            vert_scale: Scale used for occupations placement in the y axis.
        """
        self._sketch = sketch
        self._dataset = dataset
        self._vert_scale = vert_scale
        self._width = END_X_INCOME - START_X_INCOME
        self._height = END_Y_INCOME - START_Y_INCOME

        occupations = self._dataset.get_docc03_vals()

        def get_occupation_max_income(occupation):
            query = data_model.Query()
            query.set_docc03(occupation)

            query.set_female(True)
            female_income = dataset.get_wageotc(query)

            query.set_female(False)
            male_income = dataset.get_wageotc(query)

            return max([female_income, male_income])

        occupation_wages = map(get_occupation_max_income, occupations)
        max_income_unrounded = max(occupation_wages)
        self._max_income = round(max_income_unrounded)

    def draw(self):
        """Draw this subgraphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(START_X_INCOME, START_Y_INCOME)

        self._draw_axis()
        self._draw_body()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_axis(self):
        """Draw the axis labels and title."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.set_text_font(FONT, 12)
        self._sketch.clear_stroke()
        self._sketch.set_fill(DARK_TEXT_COLOR)

        self._draw_axis_top()
        self._draw_axis_bottom()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_axis_top(self):
        """Draw the axis label for median hourly income on top."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.set_text_align('center', 'bottom')
        self._sketch.draw_text(self._width / 2, 0, INCOME_TITLE)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_axis_bottom(self):
        """Draw the axis on the bottom with min and max income."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(0, self._height)

        self._sketch.set_text_align('left', 'top')
        self._sketch.draw_text(0, 0, '$0')

        self._sketch.set_text_align('right', 'top')
        self._sketch.draw_text(self._width, 0, '$%d' % self._max_income)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_body(self):
        """Draw all occupations."""
        self._sketch.push_transform()
        self._sketch.push_style()

        for occupation in self._dataset.get_docc03_vals():
            self._draw_occupation(occupation)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_occupation(self, occupation):
        """Draw a single occupation through grouped bars.

        Args:
            occupation: String occupation name matching docc03.
        """
        self._sketch.push_transform()
        self._sketch.push_style()

        y = self._vert_scale.get_position(occupation)
        self._sketch.translate(0, y)

        query = data_model.Query()
        query.set_docc03(occupation)

        query.set_female(True)
        female_income = self._dataset.get_wageotc(query)

        query.set_female(False)
        male_income = self._dataset.get_wageotc(query)

        female_width = self._get_bar_width(female_income)
        male_width = self._get_bar_width(male_income)

        self._sketch.clear_stroke()
        self._sketch.set_rect_mode('corner')

        self._sketch.set_fill(FEMALE_COLOR)
        self._sketch.draw_rect(0, -7, female_width, 5)

        self._sketch.set_fill(MALE_COLOR)
        self._sketch.draw_rect(0, 1, male_width, 5)

        self._sketch.clear_fill()
        self._sketch.set_stroke(OVERLAY_COLOR)

        for income in range(0, self._max_income, 10):
            x = self._get_bar_width(income)
            self._sketch.draw_line(x, -8, x, 7)

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _get_bar_width(self, income):
        """Get the width of an income bar.

        Args:
            income: Hourly equivalent income in USD.

        Returns:
            float: Width of bar in pixels.
        """
        percent = income / self._max_income
        return self._width * percent


if IS_ONLINE:
    sketch = sketchingpy.Sketch2D(WIDTH, HEIGHT)
else:
    sketch = sketchingpy.Sketch2DStatic(WIDTH, HEIGHT)

sketch.clear('#FFFFFF')

dataset = data_model.load_from_file(DATA_LOC, sketch=sketch)

main_presenter = MainPresenter(sketch, dataset)
main_presenter.draw()

if IS_ONLINE:
    sketch.show()
else:
    sketch.save_image('assignment_10.png')
