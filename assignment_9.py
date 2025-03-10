"""Visualization of US census data on unemployment and participation.

Submission for Assignment 9 for Stat 198: Interactive Data Science and
Visualization demonstrating 4 variables from the US Census ACS Microdata sample.

Author: A Samuel Pottinger
License: BSD-3-Clause
"""
import math

import sketchingpy

import data_model

WIDTH = 1000
HEIGHT = 1000

LEFT_PAD = 10
RIGHT_PAD = 10
TOP_PAD = 40
BOTTOM_PAD = 10
GUTTER_PAD = 10

TOP_AXIS_HEIGHT = 20
BOTTOM_AXIS_HEIGHT = 40

START_X_GENDER_PARTICIPATION = LEFT_PAD
END_X_GENDER_PARTICIPATION = START_X_GENDER_PARTICIPATION + 300
START_Y_GENDER_PARTICIPATION = TOP_PAD + TOP_AXIS_HEIGHT
END_Y_GENDER_PARTICIPATION = HEIGHT - BOTTOM_PAD - BOTTOM_AXIS_HEIGHT

START_X_UNEMPLOYMENT = END_X_GENDER_PARTICIPATION + GUTTER_PAD
START_Y_UNEMPLOYMENT = TOP_PAD + TOP_AXIS_HEIGHT
END_X_UNEMPLOYMENT = WIDTH - RIGHT_PAD
END_Y_UNEMPLOYMENT = HEIGHT - BOTTOM_PAD - BOTTOM_AXIS_HEIGHT

DARK_TEXT_COLOR = '#333333'
LIGHT_TEXT_COLOR = '#666666'
FEMALE_COLOR = '#1f78b4'
MALE_COLOR = '#33a02c'
OVERLAY_COLOR = '#FFFFFF'
OCCUPATION_AXIS_COLOR = '#E0E0E0'
GAP_COLOR = '#505050'

FONT = 'PublicSans-Regular'

TITLE = 'An Economy that Leaves Some Out'
PARTICIPATION_TITLE = '% of Workers in Occupation'

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

        def get_unemployment_for_occupation(occupation):
            query = data_model.Query()
            query.set_docc03(occupation)
            return dataset.get_unemp(query)

        occupations = dataset.get_docc03_vals()
        unemployments = map(get_unemployment_for_occupation, occupations)
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

    def draw(self):
        """Draw this graphic and its subgraphics. Includes title."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._draw_title()
        self._unemployment_presenter.draw()
        self._participation_presenter.draw()

        self._sketch.pop_style()
        self._sketch.pop_transform()

    def _draw_title(self):
        """Draw the main title at the top of the graphic."""
        self._sketch.push_transform()
        self._sketch.push_style()

        self._sketch.translate(START_X_UNEMPLOYMENT, TOP_PAD)

        self._sketch.clear_stroke()
        self._sketch.set_fill(DARK_TEXT_COLOR)

        self._sketch.set_text_font(FONT, 25)
        self._sketch.set_text_align('left', 'bottom')
        self._sketch.draw_text(0, -5, TITLE)

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
        self._sketch.draw_text(0, -20, 'Female')

        self._sketch.set_text_align('center', 'bottom')
        self._sketch.set_fill(DARK_TEXT_COLOR)
        self._sketch.draw_text(self._width / 2, -20, PARTICIPATION_TITLE)

        self._sketch.set_text_align('right', 'bottom')
        self._sketch.set_fill(MALE_COLOR)
        self._sketch.draw_text(self._width, -20, 'Male')

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
        self._sketch.draw_rect(self._width, 0, -1 * width_male, 12)

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

        self._sketch.translate(START_X_UNEMPLOYMENT, END_Y_UNEMPLOYMENT)

        self._sketch.clear_stroke()
        self._sketch.set_fill(DARK_TEXT_COLOR)
        self._sketch.set_text_align('center', 'top')
        self._sketch.set_text_font(FONT, 12)

        max_unemployment = self._horiz_scale.get_max_unemployment()
        percents = range(0, max_unemployment + 1)
        for percent in percents:
            x = self._horiz_scale.get_position(percent)
            self._sketch.draw_text(x, 0, '%d%%' % percent)

        self._sketch.draw_text(self._width / 2, 17, 'Unemployment Rate')

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

        self._sketch.set_fill(FEMALE_COLOR)
        self._sketch.draw_ellipse(female_x, 0, 10, 10)

        self._sketch.set_fill(MALE_COLOR)
        self._sketch.draw_ellipse(male_x, 0, 10, 10)

        self._sketch.pop_style()
        self._sketch.pop_transform()


sketch = sketchingpy.Sketch2DStatic(WIDTH, HEIGHT)

dataset = data_model.load_from_file(DATA_LOC, sketch=sketch)

main_presenter = MainPresenter(sketch, dataset)
main_presenter.draw()

sketch.save_image('assignment_9.png')
