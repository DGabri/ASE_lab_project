import axios from 'axios'

const register = async (email, username, password) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.post(
        'https://localhost:3000/auth/create_user',
        {
            "email": email,
            "username": username,
            "password": password,
            "user_type": 1
        },
        {
            headers: {
                'Content-Type': 'application/json'
            }
        }
    )
    
    if (response.status != 201) {
        throw new Error(JSON.stringify(response.data.err))
    }

    return response.data
}

export default register