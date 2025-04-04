import React, { useState } from 'react';
import { View, Text, TextInput, Button, Picker, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';

const App = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState({ hour: 7, minute: 0, ampm: 'AM' });
  const [diners, setDiners] = useState('1');
  const [seating, setSeating] = useState('inside');
  const [pickup, setPickup] = useState('no');

  const backendUrl = "https://la-casita-backend.onrender.com"; // Updated to your Render backend URL

  // Date Picker Logic
  const today = new Date();
  const [currentWeekStart, setCurrentWeekStart] = useState(new Date(today.setDate(today.getDate() - today.getDay())));

  const getWeekDates = (startDate) => {
    const dates = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      dates.push(date);
    }
    return dates;
  };

  const handleDateChange = (newDate) => {
    setDate(newDate.toISOString().split('T')[0]); // Format as YYYY-MM-DD
  };

  const handleWeekChange = (direction) => {
    const newStartDate = new Date(currentWeekStart);
    newStartDate.setDate(newStartDate.getDate() + (direction === 'next' ? 7 : -7));
    if (newStartDate >= new Date(new Date().setDate(new Date().getDate() - new Date().getDay()))) {
      setCurrentWeekStart(newStartDate);
    }
  };

  // Time Picker Logic
  const handleTimeChange = (type, value) => {
    setTime((prev) => ({ ...prev, [type]: value }));
  };

  const toggleAMPM = () => {
    setTime((prev) => ({ ...prev, ampm: prev.ampm === 'AM' ? 'PM' : 'AM' }));
  };

  const handleSubmit = async () => {
    const reservation = {
      name,
      email,
      phone,
      date,
      time: `${time.hour}:${time.minute} ${time.ampm}`,
      diners,
      seating,
      pickup,
    };

    try {
      const response = await fetch(`${backendUrl}/reservations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reservation),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Backend error:", errorData);
        alert(`Failed to submit reservation: ${errorData.message}`);
        return;
      }

      const data = await response.json();
      alert(data.message);
    } catch (error) {
      console.error("Frontend error:", error);
      alert('Failed to submit reservation');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text>Name:</Text>
      <TextInput value={name} onChangeText={setName} style={styles.input} />

      <Text>Email:</Text>
      <TextInput value={email} onChangeText={setEmail} style={styles.input} />

      <Text>Phone:</Text>
      <TextInput value={phone} onChangeText={setPhone} style={styles.input} />

      <Text>Date:</Text>
      <View style={styles.datePicker}>
        <View style={styles.weekDates}>
          {getWeekDates(currentWeekStart).map((dateObj, index) => (
            <View key={index} style={styles.dateContainer}>
              <TouchableOpacity
                onPress={() => handleDateChange(dateObj)}
                style={[styles.dateButton, date === dateObj.toISOString().split('T')[0] && styles.selectedDate]}
              >
                <Text>{dateObj.toLocaleDateString('en-US', { weekday: 'short' })}</Text>
                <Text>{dateObj.toLocaleDateString('en-US', { day: 'numeric' })}</Text>
              </TouchableOpacity>
              {index === 0 && (
                <TouchableOpacity onPress={() => handleWeekChange('prev')} style={styles.arrowButton}>
                  <Text style={styles.arrow}>←</Text>
                </TouchableOpacity>
              )}
              {index === 6 && (
                <TouchableOpacity onPress={() => handleWeekChange('next')} style={styles.arrowButton}>
                  <Text style={styles.arrow}>→</Text>
                </TouchableOpacity>
              )}
            </View>
          ))}
        </View>
      </View>

      <Text>Time:</Text>
      <View style={styles.timePicker}>
        <View style={styles.timeSection}>
          <Picker
            selectedValue={time.hour}
            onValueChange={(itemValue) => handleTimeChange('hour', itemValue)}
            style={styles.picker}
          >
            {[...Array(12).keys()].map((i) => (
              <Picker.Item key={i + 1} label={`${i + 1}`} value={i + 1} />
            ))}
          </Picker>
          <Text>:</Text>
          <Picker
            selectedValue={time.minute}
            onValueChange={(itemValue) => handleTimeChange('minute', itemValue)}
            style={styles.picker}
          >
            {[...Array(60).keys()].map((i) => (
              <Picker.Item key={i} label={`${i.toString().padStart(2, '0')}`} value={i} />
            ))}
          </Picker>
          <Picker
            selectedValue={time.ampm}
            onValueChange={(itemValue) => handleTimeChange('ampm', itemValue)}
            style={styles.picker}
          >
            <Picker.Item label="AM" value="AM" />
            <Picker.Item label="PM" value="PM" />
          </Picker>
        </View>
      </View>

      <Text>Number of Diners:</Text>
      <Picker selectedValue={diners} onValueChange={setDiners}>
        {[...Array(10).keys()].map((i) => (
          <Picker.Item key={i + 1} label={`${i + 1}`} value={`${i + 1}`} />
        ))}
      </Picker>

      <Text>Seating Preference:</Text>
      <Picker selectedValue={seating} onValueChange={setSeating}>
        <Picker.Item label="Inside" value="inside" />
        <Picker.Item label="Outside" value="outside" />
      </Picker>

      <Text>Require Pickup and Drop-off?</Text>
      <Picker selectedValue={pickup} onValueChange={setPickup}>
        <Picker.Item label="No" value="no" />
        <Picker.Item label="Yes" value="yes" />
      </Picker>

      <Button title="Submit Reservation" onPress={handleSubmit} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    marginBottom: 10,
  },
  datePicker: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  weekDates: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flex: 1,
    marginHorizontal: 10,
  },
  dateContainer: {
    alignItems: 'center',
  },
  dateButton: {
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
    alignItems: 'center',
  },
  selectedDate: {
    backgroundColor: '#ddd',
  },
  arrowButton: {
    padding: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 5,
    marginTop: 10,
  },
  arrow: {
    fontSize: 24,
  },
  timePicker: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  timeSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    flex: 1,
  },
  picker: {
    width: 100,
    height: 150,
  },
});

export default App;
