import axios from 'axios'

const getPull = async (access_token, banner_id) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.get(
        `https://localhost:3000/banner/banner/pull/${banner_id}`,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )

    if (response.status != 200) {
        throw new Error(response.data.message)  
    }
    
    return response.data.pieces
}

export default getPull