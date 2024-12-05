import axios from 'axios'

const login = async (username, password) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.post(
        'https://localhost:3000/auth/login',
        {
            "username": username,
            "password": password
        },
        {
            headers: {
                'Content-Type': 'application/json'
            }
        }
    )
    
    if (response.status != 200) {
        throw new Error(response.data.err)  
    }

    return response.data
}

export default login