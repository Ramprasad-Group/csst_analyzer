
from csst.analyzer.models import AverageTransmission



'''
def average_transmission_at_temp(
    temp: float, temp_range: float = 0
) -> List[AverageTransmission]:
    """ "Returns the average transmission at temperature for each reactor

    :parameter temp: Temperature to average at.
    :type temp: float
    :parameter temp_range: When assessing transmissions at this temp,
        look at rows with temp +- (temp_range / 2)
    :type temp_range: float:
    :return: List of AverageTransmission objects
    :rtype: List[AverageTransmission]
    """
    temp_col = [col for col in self.df.columns if "Temperature Actual" in col][0]
    reactor_cols = [
        col
        for col in self.df.columns
        for reactor in self.samples.keys()
        if reactor in col
    ]
    temp_range /= 2
    temp_df = self.df.loc[
        (self.df[temp_col] >= (temp - temp_range))
        & (self.df[temp_col] <= (temp + temp_range))
    ]
    average_transmissions = []
    for reactor_col in reactor_cols:
        sample = [col for col in self.samples.keys() if col in reactor_col][0]
        # In data, most sig figs I've seen is 4, so round to 2 decimal
        # places
        mean = round(temp_df[reactor_col].mean(), 2)
        std = round(temp_df[reactor_col].std(), 2)
        transmissions = temp_df[reactor_col].to_list()
        average_transmissions.append(
            AverageTransmission(
                reactor=sample,
                temp=temp,
                temp_range=temp_range * 2,
                average_transmission=mean,
                std=std,
                transmissions=transmissions,
            )
        )
    return average_transmissions
'''
